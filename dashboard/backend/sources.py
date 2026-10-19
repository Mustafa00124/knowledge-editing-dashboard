"""Everything a checkout can download, and what is already on disk.

Three kinds of item:
  - datasets:   one per datasets/<name>/SOURCE.json, a pinned list of file
                URLs with sha256s, plus archives to unpack and derived files
                to build after downloading (see _build)
  - models:     models_reader.CATALOG, fetched from Hugging Face
  - components: EasyEdit and the experiment Python environment

Standard library only. scripts/setup.py imports this before any environment
exists, and the dashboard backend uses it for the Downloads page, so both
agree on what "installed" means. The download functions print progress
lines and raise on failure; callers decide how to surface that.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import models_reader  # noqa: E402

ROOT = config.PROJECT_ROOT
DATASETS_DIR = ROOT / "datasets"
MODELS_DIR = ROOT / "models"
EXTERNAL_DIR = ROOT / "external"
VENV = ROOT / "venvs" / "easyedit_venv"
VENV_PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


# The only external repo the runner imports; see scripts/setup.py for the
# reference repos the dynamic/ methods were ported from.
EASYEDIT = {
    "url": "https://github.com/zjunlp/EasyEdit.git",
    "commit": "14cea8245f06715684592ab55184939b99d70784",
    "patches": ["patches/EasyEdit-alphaedit-fixes.patch", "patches/EasyEdit-long-context-stats-cap.patch"],
    "bytes": 200_000_000,
}
# CaKE's upstream repo, for its released circuit-guided training data
# (datasets/*-cake.json). The method itself is experiments/run_experiment/cake.py.
CAKE = {
    "url": "https://github.com/zjunlp/CaKE.git",
    "commit": "df528e13fffbd2117e6041c129285e1e146933d2",
    "bytes": 44_000_000,
}
# Ollama, for the optional local judge of the known-fact check
# (experiments/causal_tracing/knowledge.py): the official Linux build,
# unpacked into external/ollama; models it pulls go to external/ollama/models.
OLLAMA = {
    "version": "v0.35.1",
    "url": "https://github.com/ollama/ollama/releases/download/v0.35.1/ollama-linux-amd64.tar.zst",
    "sha256": "9fcd79ac4575b2bd31b992eee18b1000c8ad126b451627c8f8cd091714cfbb10",
    "bytes": 1_439_658_961,
}
REQUIREMENTS = [
    "external/EasyEdit/requirements.txt",
    "experiments/run_experiment/requirements-evaluation.txt",
]
# What pip leaves in venvs/easyedit_venv on Linux with CUDA wheels. Only a
# disk-space estimate: pip reports no size before it starts.
VENV_BYTES = 6_500_000_000

COMPONENTS = {
    "easyedit": {
        "label": "EasyEdit",
        "description": "The editing library every method runs through, at the pinned commit with this project's AlphaEdit fix applied.",
        "bytes": EASYEDIT["bytes"],
    },
    "cake-data": {
        "label": "CaKE training data",
        "description": "CaKE's released circuit-guided training examples for MQuAKE, needed only to run the CaKE method.",
        "bytes": CAKE["bytes"],
    },
    "ollama": {
        "label": "Ollama (local judge)",
        "description": "Runs a small local model as the judge of the known-fact check (fact selection and tracing, --judge ollama). Optional.",
        "bytes": OLLAMA["bytes"],
    },
    "experiment-env": {
        "label": "Experiment Python environment",
        "description": "venvs/easyedit_venv: PyTorch, transformers and EasyEdit's requirements. A large pip install; needs EasyEdit first.",
        "bytes": VENV_BYTES,
        "requires": ["easyedit"],
    },
}


def say(message):
    print(message, flush=True)


# ---------------------------------------------------------------- datasets


def dataset_names():
    if not DATASETS_DIR.exists():
        return []
    return sorted(p.parent.name for p in DATASETS_DIR.glob("*/SOURCE.json"))


def manifest(name):
    return json.loads((DATASETS_DIR / name / "SOURCE.json").read_text())


def _files(m, parts=()):
    return [f for f in m["files"] if not f.get("part") or f["part"] in parts]


def _file_present(root, entry):
    path = root / entry["path"]
    return path.is_file() and path.stat().st_size == entry["bytes"]


def _members(z):
    """Archive entries worth unpacking: macOS metadata (__MACOSX/, .DS_Store)
    that some releases were zipped with is skipped."""
    return [n for n in z.namelist() if not n.startswith("__MACOSX/") and not n.endswith(".DS_Store")]


def _extracted(root, archive):
    try:
        with zipfile.ZipFile(root / archive) as z:
            return all((root / n).exists() for n in _members(z))
    except (OSError, zipfile.BadZipFile):
        return False


def _built(root, step):
    return {"views": (root / "VIEWS.json").exists(),
            "realtimeqa": (root / "realtimeqa_editing.json").exists(),
            "ruleedit": (root / "ruleedit_editing.json").exists()}[step]


def dataset_status(name):
    m = manifest(name)
    root = DATASETS_DIR / name
    required = _files(m)
    present = [f for f in required if _file_present(root, f)]
    complete = (
        len(present) == len(required)
        and all(_extracted(root, a) for a in m.get("extract", []))
        # RuleEdit-200's views are skipped upstream-side (malformed records),
        # so a missing VIEWS.json there does not mean incomplete. Its editing
        # file, which the runner loads, does.
        and all(_built(root, s) for s in m.get("build", [])
                if not (name == "RuleEdit-200" and s == "views"))
    )
    parts = {}
    for key, label in m.get("parts", {}).items():
        files = [f for f in m["files"] if f.get("part") == key]
        parts[key] = {
            "label": label,
            "bytes": sum(f["bytes"] for f in files),
            "installed": all(_file_present(root, f) for f in files),
        }
    return {
        "name": name,
        "repository": m.get("repository"),
        "bytes": sum(f["bytes"] for f in required),
        "present_bytes": sum(f["bytes"] for f in present),
        "installed": complete,
        "partial": bool(present) and not complete,
        "parts": parts,
    }


def _fetch(url, dest, expected_sha, expected_bytes, attempts=3):
    tmp = dest.with_name(dest.name + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, attempts + 1):
        try:
            digest = hashlib.sha256()
            request = urllib.request.Request(url, headers={"User-Agent": "knowledge-editing-setup"})
            with urllib.request.urlopen(request, timeout=60) as response, open(tmp, "wb") as out:
                for chunk in iter(lambda: response.read(1 << 20), b""):
                    out.write(chunk)
                    digest.update(chunk)
            if digest.hexdigest() != expected_sha or tmp.stat().st_size != expected_bytes:
                raise ValueError(f"checksum mismatch for {url}")
            os.replace(tmp, dest)
            return
        except (OSError, ValueError, urllib.error.URLError) as exc:
            tmp.unlink(missing_ok=True)
            if attempt == attempts:
                raise RuntimeError(f"could not download {url}: {exc}") from exc
            say(f"    retrying ({exc})")
            time.sleep(2 * attempt)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build(name, step):
    if step == "views":
        script = ROOT / "dashboard" / "scripts" / "prepare_benchmarks.py"
        subprocess.run([sys.executable, str(script), name], check=True)
    elif step in ("realtimeqa", "ruleedit"):
        subprocess.run([sys.executable, "build_editing_set.py"], cwd=DATASETS_DIR / name, check=True)


def download_dataset(name, parts=()):
    m = manifest(name)
    root = DATASETS_DIR / name
    files = _files(m, parts)
    total = sum(f["bytes"] for f in files)
    say(f"== dataset {name}: {len(files)} files, {total / 1e6:.1f} MB from {m.get('repository')}")
    done = 0
    for entry in files:
        dest = root / entry["path"]
        if _file_present(root, entry) and _sha256(dest) == entry["sha256"]:
            done += entry["bytes"]
            continue
        _fetch(entry["url"], dest, entry["sha256"], entry["bytes"])
        done += entry["bytes"]
        say(f"  {entry['path']} ({done / 1e6:.1f} / {total / 1e6:.1f} MB)")
    for archive in m.get("extract", []):
        say(f"  unpacking {archive}")
        with zipfile.ZipFile(root / archive) as z:
            members = _members(z)
            for member in members:
                target = (root / member).resolve()
                if root.resolve() not in target.parents and target != root.resolve():
                    raise RuntimeError(f"{archive} contains a path outside the dataset folder: {member}")
            z.extractall(root, members)
    for step in m.get("build", []):
        say(f"  building {step}")
        _build(name, step)
    say(f"  {name} ready")


# ---------------------------------------------------------------- models


def model_status(model):
    path = MODELS_DIR / model["name"]
    return {
        "installed": models_reader.installed(path),
        "present_bytes": _tree_bytes(path),
    }


def _tree_bytes(path):
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def hf_python():
    """An interpreter that can import huggingface_hub, preferring this one
    (the dashboard backend installs it) over the experiment venv."""
    candidates = [sys.executable] + ([str(VENV_PYTHON)] if VENV_PYTHON.exists() else [])
    for python in candidates:
        if subprocess.run([python, "-c", "import huggingface_hub"], capture_output=True).returncode == 0:
            return python
    raise RuntimeError("huggingface_hub is not installed: `pip install huggingface_hub`, "
                       "or create the experiment environment first")


_MODEL_DOWNLOAD = r"""
import fnmatch, sys
from huggingface_hub import HfApi, snapshot_download
repo, dest, ignore = sys.argv[1], sys.argv[2], sys.argv[3].split("|")
files = HfApi().list_repo_files(repo)
if any(f.endswith(".safetensors") for f in files):
    ignore += ["*.bin", "*.pth"]
snapshot_download(repo_id=repo, local_dir=dest, ignore_patterns=ignore)
"""


def download_model(name):
    model = next((m for m in models_reader.CATALOG if m["name"].lower() == name.lower()), None)
    if model is None:
        raise RuntimeError(f"unknown model {name}; choose from: " + ", ".join(m["name"] for m in models_reader.CATALOG))
    dest = MODELS_DIR / model["name"]
    if models_reader.installed(dest):
        say(f"== model {model['name']} already downloaded")
        _convert_tokenizer(model, dest)
        return
    size = models_reader.DOWNLOAD_BYTES.get(model["name"])
    say(f"== model {model['name']} from huggingface.co/{model['repo_id']}"
        + (f" ({size / 1e9:.1f} GB)" if size else ""))
    if model.get("gated"):
        say("  gated model: this needs an accepted license on huggingface.co and a login (`hf auth login`)")
    # The directory name matters: hparams/*.yaml point at models/<name>, and
    # cached covariance statistics are keyed by it.
    subprocess.run([hf_python(), "-c", _MODEL_DOWNLOAD, model["repo_id"], str(dest),
                    "|".join(models_reader.DOWNLOAD_IGNORE)], check=True)
    if not models_reader.installed(dest):
        raise RuntimeError(f"{model['name']} finished downloading but has no config.json and weights")
    _convert_tokenizer(model, dest)
    say(f"  {model['name']} ready")


def _convert_tokenizer(model, dest):
    """MAP-Neo's tokenizer is custom code; write a stock one in its place so
    nothing needs trust_remote_code. A no-op once done."""
    if not model.get("convert_tokenizer"):
        return
    if not VENV_PYTHON.exists():
        raise RuntimeError(f"{model['name']} needs its tokenizer converted, which runs in the experiment "
                           "environment: create it (--venv), then run this again")
    subprocess.run([str(VENV_PYTHON), str(ROOT / "scripts" / "convert_neo_tokenizer.py"), str(dest)], check=True)


# ---------------------------------------------------------------- components


# Written into the venv once pip has installed everything, so a venv that
# exists but whose install failed or is still running does not count.
VENV_MARKER = VENV / ".ke-install-complete"


def experiment_env_ready():
    if VENV_MARKER.exists():
        return True
    if (VENV.parent / ".pip-tmp").exists():
        return False  # an install is running (or died) and has not finished
    # Environments built before the marker existed (gaivi's) count when
    # PyTorch is installed in them.
    return any(VENV.glob("lib/python3*/site-packages/torch")) or (VENV / "Lib/site-packages/torch").exists()


def component_status(key):
    if key == "easyedit":
        path = EXTERNAL_DIR / "EasyEdit"
        return {"installed": (path / "easyeditor").is_dir(), "present_bytes": 0}
    if key == "cake-data":
        return {"installed": (EXTERNAL_DIR / "CaKE" / "datasets").is_dir(), "present_bytes": 0}
    if key == "ollama":
        return {"installed": (EXTERNAL_DIR / "ollama" / "bin" / "ollama").exists(), "present_bytes": 0}
    if key == "experiment-env":
        return {"installed": experiment_env_ready(), "partial": VENV_PYTHON.exists() and not experiment_env_ready(),
                "present_bytes": 0}
    raise KeyError(key)


def _git_checkout(url, commit, dest):
    if (dest / ".git").exists():
        current = subprocess.run(["git", "rev-parse", "HEAD"], cwd=dest, capture_output=True, text=True).stdout.strip()
        if current != commit:
            say(f"  {dest.relative_to(ROOT)} is at {current[:10]}, not the pinned {commit[:10]}; leaving it alone")
        else:
            say(f"  {dest.relative_to(ROOT)} already at {commit[:10]}")
        return False
    if not shutil.which("git"):
        raise RuntimeError("git is required to fetch EasyEdit")
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--quiet", url, str(dest)], check=True)
    subprocess.run(["git", "-c", "advice.detachedHead=false", "checkout", "--quiet", commit], cwd=dest, check=True)
    return True


def git_checkout_with_patches(url, commit, dest, patches=()):
    fresh = _git_checkout(url, commit, dest)
    for patch in patches:
        patch_path = str(ROOT / patch)
        check = lambda *flags: subprocess.run(["git", "apply", "--check", *flags, patch_path], cwd=dest,
                                              capture_output=True).returncode == 0
        if check("-R"):
            say(f"  {patch} already applied")
        elif fresh or check():
            subprocess.run(["git", "apply", patch_path], cwd=dest, check=True)
            say(f"  applied {patch}")
        else:
            say(f"  WARNING: {patch} does not apply to {dest.relative_to(ROOT)}; apply it by hand")


def install_easyedit():
    say("== EasyEdit")
    git_checkout_with_patches(EASYEDIT["url"], EASYEDIT["commit"], EXTERNAL_DIR / "EasyEdit", EASYEDIT["patches"])
    say("  EasyEdit ready")


def _base_python():
    """A Python 3.10+ to build the environment from: the pinned PyTorch has no
    wheels for older versions. This interpreter when new enough (the project
    uses 3.11), otherwise the newest python3.1x on PATH."""
    if sys.version_info >= (3, 10):
        return sys.executable
    for name in ("python3.13", "python3.12", "python3.11", "python3.10"):
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError(
        f"the experiment environment needs Python 3.10 or newer, and this is {sys.version.split()[0]} "
        "with no python3.10+ on PATH. Install one (3.11 is what the project uses) and try again."
    )


def install_ollama():
    say(f"== Ollama {OLLAMA['version']}")
    dest = EXTERNAL_DIR / "ollama"
    if (dest / "bin" / "ollama").exists():
        say("  already installed")
        return
    if not shutil.which("zstd"):
        raise RuntimeError("unpacking Ollama needs zstd on PATH")
    archive = EXTERNAL_DIR / "ollama-linux-amd64.tar.zst"
    if not archive.exists():
        _fetch(OLLAMA["url"], archive, OLLAMA["sha256"], OLLAMA["bytes"])
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tar", "--use-compress-program=zstd -d", "-xf", str(archive), "-C", str(dest)], check=True)
    archive.unlink()
    (dest / "models").mkdir(exist_ok=True)
    say(f"  Ollama ready in {dest}")


def install_cake_data():
    say("== CaKE training data")
    git_checkout_with_patches(CAKE["url"], CAKE["commit"], EXTERNAL_DIR / "CaKE")
    say("  CaKE training data ready")


def install_experiment_env():
    say("== experiment environment (venvs/easyedit_venv)")
    missing = [r for r in REQUIREMENTS if not (ROOT / r).exists()]
    if missing:
        raise RuntimeError(f"missing {', '.join(missing)}: download EasyEdit first")
    if not VENV_PYTHON.exists():
        base = _base_python()
        say(f"  creating it with {base}")
        subprocess.run([base, "-m", "venv", str(VENV)], check=True)
    # pip unpacks wheels in TMPDIR, and PyTorch's CUDA wheels need several GB
    # there: more than a small /tmp (gaivi's is a 2 GB RAM disk) holds. A
    # scratch folder beside the venv lives on the same disk as the result.
    scratch = VENV.parent / ".pip-tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "TMPDIR": str(scratch), "TEMP": str(scratch), "TMP": str(scratch)}
    try:
        subprocess.run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"], check=True, env=env)
        args = [str(VENV_PYTHON), "-m", "pip", "install"]
        for requirement in REQUIREMENTS:
            args += ["-r", str(ROOT / requirement)]
        subprocess.run(args, check=True, env=env)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    VENV_MARKER.write_text("pip install finished\n")
    say("  experiment environment ready")


# ---------------------------------------------------------------- catalog


def catalog():
    """Every downloadable item with its size and on-disk status."""
    items = []
    for key, component in COMPONENTS.items():
        items.append({"kind": "component", "name": key, **component, **component_status(key)})
    for name in dataset_names():
        status = dataset_status(name)
        items.append({"kind": "dataset", "label": name, **status})
    for model in models_reader.CATALOG:
        items.append({
            "kind": "model",
            "name": model["name"],
            "label": model["name"],
            "repository": f"https://huggingface.co/{model['repo_id']}",
            "bytes": models_reader.DOWNLOAD_BYTES.get(model["name"]),
            "parameters_b": model["parameters_b"],
            "family": model["family"],
            "model_type": model["model_type"],
            "main": model.get("main", False),
            "gated": model.get("gated", False),
            **model_status(model),
        })
    return items


def disk_free_bytes():
    return shutil.disk_usage(ROOT).free
