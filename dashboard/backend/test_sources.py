"""The download catalog (sources.py) and the Downloads page's task layer.

Downloads run offline here: a throwaway dataset whose manifest points at
file:// URLs, so checksum checks, resuming, archive unpacking and optional
parts are exercised without the network. The real manifests are checked
for shape, not fetched (a full fetch is ~1.5 GB).
"""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import downloads
import models_reader
import sources


def entry(root, rel, **extra):
    path = root / rel
    return {"path": rel, "url": path.resolve().as_uri(), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), **extra}


class RealManifestTests(unittest.TestCase):
    def test_every_manifest_is_complete(self):
        names = sources.dataset_names()
        self.assertGreaterEqual(len(names), 15)
        for name in names:
            m = sources.manifest(name)
            with self.subTest(dataset=name):
                self.assertTrue(m["files"])
                paths = {f["path"] for f in m["files"]}
                for f in m["files"]:
                    self.assertTrue(f["url"].startswith("https://"), f["path"])
                    self.assertEqual(len(f["sha256"]), 64, f["path"])
                    self.assertIsInstance(f["bytes"], int)
                    self.assertNotIn(" ", f["url"], "URLs must be percent-encoded")
                for archive in m.get("extract", []):
                    self.assertIn(archive, paths)
                for step in m.get("build", []):
                    self.assertIn(step, ("views", "realtimeqa", "ruleedit"))
                for f in m["files"]:
                    if f.get("part"):
                        self.assertIn(f["part"], m.get("parts", {}))

    def test_every_catalog_model_has_a_download_size(self):
        for model in models_reader.CATALOG:
            self.assertIn(model["name"], models_reader.DOWNLOAD_BYTES)


class DownloadDatasetTests(unittest.TestCase):
    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.upstream = tmp / "upstream"
        self.upstream.mkdir()
        (self.upstream / "data.json").write_text(json.dumps([{"prompt": "p", "target_new": "t"}]))
        with zipfile.ZipFile(self.upstream / "bundle.zip", "w") as z:
            z.writestr("bundle/inner.json", "[]")
            z.writestr("__MACOSX/bundle/._inner.json", "junk")
        (self.upstream / "extra").mkdir()
        (self.upstream / "extra" / "big.json").write_text("[1, 2, 3]")

        self.datasets = tmp / "datasets"
        self.root = self.datasets / "Toy"
        self.root.mkdir(parents=True)
        self.manifest = {
            "repository": "local", "files": [
                entry(self.upstream, "data.json"),
                entry(self.upstream, "bundle.zip"),
                entry(self.upstream, "extra/big.json", part="extra"),
            ],
            "extract": ["bundle.zip"],
            "parts": {"extra": "Extra split"},
        }
        (self.root / "SOURCE.json").write_text(json.dumps(self.manifest))
        patcher = mock.patch.object(sources, "DATASETS_DIR", self.datasets)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_download_unpacks_and_reports_installed(self):
        self.assertFalse(sources.dataset_status("Toy")["installed"])
        sources.download_dataset("Toy")
        status = sources.dataset_status("Toy")
        self.assertTrue(status["installed"])
        self.assertTrue((self.root / "bundle" / "inner.json").exists())
        self.assertFalse((self.root / "__MACOSX").exists(), "macOS archive junk is skipped")
        self.assertFalse(status["parts"]["extra"]["installed"], "optional parts stay opt-in")

    def test_optional_part_downloads_when_asked(self):
        sources.download_dataset("Toy", ["extra"])
        self.assertTrue(sources.dataset_status("Toy")["parts"]["extra"]["installed"])

    def test_checksum_mismatch_is_refused_and_leaves_nothing(self):
        self.manifest["files"][0]["sha256"] = "0" * 64
        (self.root / "SOURCE.json").write_text(json.dumps(self.manifest))
        with mock.patch.object(sources.time, "sleep"):
            with self.assertRaises(RuntimeError):
                sources.download_dataset("Toy")
        self.assertFalse((self.root / "data.json").exists())
        self.assertFalse(list(self.root.glob("*.part")))

    def test_partial_download_resumes_without_refetching(self):
        sources.download_dataset("Toy")
        (self.root / "bundle.zip").unlink()
        self.assertTrue(sources.dataset_status("Toy")["partial"])
        with mock.patch.object(sources, "_fetch", wraps=sources._fetch) as fetch:
            sources.download_dataset("Toy")
        self.assertEqual([c.args[1].name for c in fetch.call_args_list], ["bundle.zip"])


class DownloadTaskTests(unittest.TestCase):
    def test_selection_larger_than_free_space_is_refused(self):
        with mock.patch.object(sources, "disk_free_bytes", return_value=1):
            missing = next(i for i in sources.catalog() if i["kind"] == "model" and not i["installed"])
            with self.assertRaisesRegex(ValueError, "not enough disk space"):
                downloads.start([{"kind": "model", "name": missing["name"]}])

    def test_unknown_item_is_refused(self):
        with self.assertRaises(KeyError):
            downloads.start([{"kind": "dataset", "name": "NoSuchBenchmark"}])


if __name__ == "__main__":
    unittest.main()
