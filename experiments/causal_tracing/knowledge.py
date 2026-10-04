"""Does a model know a fact? Shared by fact selection and the tracers.

--known_check generate: the model answers the prompt in up to
--answer_tokens greedy tokens, and knows the fact when an accepted answer
(the dataset's answer or an alias, case-insensitive, as whole words) appears
in what it wrote. With --judge, an answer that does not contain one is asked
to a judge model, which may accept an equivalent ("NYC" for "New York City")
and quotes where the answer says it.

Whatever the model wrote before the answer is its lead-in ("The capital is"
in "The capital is Paris"). Tracing runs on prompt + lead-in, so the traced
token is the answer's first token at the point the model actually produces
it. Fact selection records each fact's lead-in per model and format in the
fact set, and the tracers reuse it rather than generating again. The traced
token must still be the model's top choice there with probability
>= --min_prob (causal_trace.recall_target).

--known_check first_token (the default until generate has been checked on
GPU runs) is the original test: the answer's first token must be the
model's very next token.

Judges: "local" (the default) loads --judge_model, by default
Qwen3-4B-Instruct-2507 from models/, with transformers on the job's own GPU
and judges in batches. "ollama" starts a local Ollama server inside the job
(external/ollama, installed by `scripts/setup.py --ollama`) and runs
qwen3:4b-instruct by default; KE_OLLAMA_URL points at an already running
server instead. "api" uses the OpenAI-compatible judge of
experiments/run_experiment/evaluation.local.json (or KE_JUDGE_* variables).
--compare_judge also asks a second judge the same cases and records the
time each took and how often they agreed (fact selection's summary).
"""
import atexit
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import torch

import formats as F

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLLAMA_DIR = os.path.join(PROJECT_ROOT, "external", "ollama")
DEFAULT_JUDGE_MODELS = {"local": "qwen3-4b-instruct-2507", "ollama": "qwen3:4b-instruct", "api": ""}

# Set by a tracer's main(): the judge, and the fact set's lead-ins for the
# traced model and format (fact id -> lead-in). Kept here rather than on the
# argparse namespace, which is written out as the run's settings.
STATE = {"judge": None, "lead_ins": None}
JUDGES = ("none", "local", "ollama", "api")


def add_arguments(p):
    p.add_argument("--known_check", choices=("generate", "first_token"), default="first_token",
                   help="generate: the model answers and must say an accepted answer; first_token: the "
                        "answer's first token must be its very next token")
    p.add_argument("--answer_tokens", type=int, default=24, help="tokens the model may write when answering")
    p.add_argument("--judge", choices=JUDGES, default="local",
                   help="ask a judge model about answers that do not contain an accepted answer")
    p.add_argument("--judge_model", default="",
                   help="the judge's model (local: a model key or path, default qwen3-4b-instruct-2507; "
                        "ollama: default qwen3:4b-instruct)")
    p.add_argument("--compare_judge", choices=JUDGES, default="none",
                   help="also ask this judge every case, to compare time and agreement (not used for the result)")


# ---------------------------------------------------------------- answers

def find_answer(text, answers):
    """Where the earliest accepted answer starts in text (case-insensitive,
    not inside a longer word), or None."""
    best = None
    for answer in answers:
        answer = answer.strip()
        if not answer:
            continue
        pattern = (r"(?<!\w)" if answer[0].isalnum() else "") + re.escape(answer) + \
                  (r"(?!\w)" if answer[-1].isalnum() else "")
        match = re.search(pattern, text, re.IGNORECASE)
        if match and (best is None or match.start() < best):
            best = match.start()
    return best


def with_lead_in(item, lead_in):
    """The item with the model's lead-in appended to its prompt. Corruption
    spans index the original text, which stays a prefix, so they still hold."""
    lead_in = (lead_in or "").rstrip()
    return {**item, "text": item["text"] + lead_in, "lead_in": lead_in}


def query_text(row, item):
    """The prompt as a person would read it, for the judge: the question or
    cloze rather than chat-template markup."""
    return row.get("question") or row.get("cloze") or item["text"]


# ---------------------------------------------------------------- model passes

def _padded(tok, items):
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    ids = [F.encode(tok, item)["input_ids"] for item in items]
    width = max(len(x) for x in ids)
    input_ids = torch.tensor([[pad] * (width - len(x)) + x for x in ids])
    mask = torch.tensor([[0] * (width - len(x)) + [1] * len(x) for x in ids])
    return input_ids, mask, pad


def generate(model, tok, items, device, max_new_tokens, batch_size=16):
    """Greedy answers, one string per item (left-padded batches)."""
    out = []
    for start in range(0, len(items), batch_size):
        input_ids, mask, pad = _padded(tok, items[start:start + batch_size])
        with torch.no_grad():
            generated = model.generate(input_ids=input_ids.to(device), attention_mask=mask.to(device),
                                       max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=pad,
                                       temperature=None, top_p=None, top_k=None)
        out.extend(tok.decode(row, skip_special_tokens=True) for row in generated[:, input_ids.shape[1]:])
    return out


def next_token_probs(model, tok, items, device, batch_size=16):
    """(index, next-token probabilities) per item, in batches."""
    for start in range(0, len(items), batch_size):
        input_ids, mask, _ = _padded(tok, items[start:start + batch_size])
        with torch.no_grad():
            logits = model(input_ids=input_ids.to(device), attention_mask=mask.to(device)).logits[:, -1].float()
        for offset, row in enumerate(torch.softmax(logits, dim=-1)):
            yield start + offset, row


# ---------------------------------------------------------------- the check

def check(rows, items, generations, judge=None, compare=None):
    """{"known", "how", "lead_in", "generation"} per (row, item, answer):
    how is "match" (an accepted answer appears), "judge" (the judge accepted
    an equivalent and quoted it) or "none"."""
    results = []
    for row, item, generation in zip(rows, items, generations):
        at = find_answer(generation, item["answers"])
        if at is not None:
            results.append({"known": True, "how": "match", "lead_in": generation[:at], "generation": generation})
        else:
            results.append({"known": False, "how": "none", "lead_in": None, "generation": generation})
    if judge is not None:
        misses = [i for i, r in enumerate(results) if not r["known"] and results[i]["generation"].strip()]
        cases = [(query_text(rows[i], items[i]), results[i]["generation"], items[i]["answers"]) for i in misses]
        verdicts = judge.many(cases)
        if compare is not None:
            other = compare.many(cases)
            compare.agreed += sum((a is None) == (b is None) for a, b in zip(verdicts, other))
        for i, span in zip(misses, verdicts):
            if span:
                at = results[i]["generation"].lower().find(span.lower())
                results[i].update(known=True, how="judge", lead_in=results[i]["generation"][:at])
    return results


def prepare(model, tok, device, row, item, args):
    """For a tracer: the item to trace (the lead-in appended), or None when
    the model does not know the fact. The fact set's lead-in is used when
    there is one; otherwise the model answers here."""
    if item is None or getattr(args, "known_check", "first_token") == "first_token":
        return item
    stored = STATE["lead_ins"]
    if stored is not None and row.get("id") in stored:
        return with_lead_in(item, stored[row["id"]])
    generation = generate(model, tok, [item], device, args.answer_tokens)
    result = check([row], [item], generation, STATE["judge"])[0]
    return with_lead_in(item, result["lead_in"]) if result["known"] else None


def setup(args, fact_set=None, model_key=None, fmt=None):
    """A tracer's main(): start the judge and load the fact set's lead-ins."""
    STATE["judge"] = make_judge(args) if getattr(args, "known_check", "first_token") == "generate" else None
    lead_ins = ((fact_set or {}).get("lead_ins") or {}).get(model_key, {}).get(fmt)
    STATE["lead_ins"] = lead_ins if lead_ins else None


# ---------------------------------------------------------------- judges

JUDGE_PROMPT = """You check whether a model's answer gives the reference answer.

Prompt: {prompt}
Model's answer: {answer}
Reference answers (any one counts, as does an equivalent name, abbreviation or spelling): {references}

Does the model's answer give a reference answer? Reply with JSON only, in this form:
{{"correct": true or false, "span": "the exact words in the model's answer that give it, or empty"}}"""


def _verdict(text, answer):
    """The quoted span when the judge says correct and the span is really in
    the answer; None otherwise."""
    try:
        start, end = text.index("{"), text.rindex("}") + 1
        data = json.loads(text[start:end])
    except ValueError:
        return None
    span = str(data.get("span") or "").strip()
    if data.get("correct") is True and span and span.lower() in answer.lower():
        return span
    return None


class Judge:
    """many([(prompt, answer, references)]) -> span or None each, in parallel."""

    def __init__(self, ask, model, workers=8):
        self.ask, self.model, self.workers = ask, model, workers
        self.calls = self.seconds = self.errors = self.agreed = 0
        self.load_seconds = None  # starting the judge (a server, or loading weights), timed apart from the calls

    def stats(self):
        return {"model": self.model, "calls": self.calls, "errors": self.errors, "seconds": round(self.seconds, 1),
                "load_seconds": self.load_seconds,
                "seconds_per_call": round(self.seconds / self.calls, 4) if self.calls else None}

    def one(self, prompt, answer, references):
        text = JUDGE_PROMPT.format(prompt=prompt, answer=answer.strip(), references="; ".join(references))
        try:
            return _verdict(self.ask(text), answer)
        except Exception as exc:  # a failed call is a "no"; counted, and reported in the run's summary
            self.errors += 1
            print(f"judge call failed: {exc}", file=sys.stderr, flush=True)
            return None

    def many(self, cases):
        if not cases:
            return []
        began = time.time()
        with ThreadPoolExecutor(self.workers) as pool:
            out = list(pool.map(lambda case: self.one(*case), cases))
        self.calls += len(cases)
        self.seconds += time.time() - began
        return out


class LocalJudge(Judge):
    """A chat model loaded with transformers on this job's GPU, answering
    the judge prompt for a batch of cases at a time. Loaded on first use, so
    a run whose answers all match never loads it."""

    def __init__(self, name, device, batch_size=16):
        super().__init__(None, f"local:{name}")
        self.name, self.device, self.batch_size = name, device, batch_size
        self.tok = self.lm = None

    def _load(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import causal_trace as ct  # here, not at the top: causal_trace imports this module
        path = ct.MODEL_PATHS.get(self.name, self.name)
        self.tok = AutoTokenizer.from_pretrained(path)
        self.lm = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16).to(self.device).eval()

    def many(self, cases):
        if not cases:
            return []
        if self.lm is None:
            loading = time.time()
            self._load()
            self.load_seconds = round(time.time() - loading, 1)
        began = time.time()
        items = [{"text": self.tok.apply_chat_template(
                      [{"role": "user", "content": JUDGE_PROMPT.format(
                          prompt=prompt, answer=answer.strip(), references="; ".join(references))}],
                      tokenize=False, add_generation_prompt=True), "templated": True}
                 for prompt, answer, references in cases]
        replies = generate(self.lm, self.tok, items, self.device, 60, self.batch_size)
        out = [_verdict(reply, answer) for reply, (_, answer, _) in zip(replies, cases)]
        self.calls += len(cases)
        self.seconds += time.time() - began
        return out


def _post(url, payload, timeout):
    request = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:  # say what the server said, not just its status
        raise RuntimeError(f"{url}: HTTP {exc.code}: {exc.read().decode(errors='replace')[:500]}") from exc


class OllamaServer:
    """`ollama serve` inside this job, on a free local port, stopped at exit."""

    def __init__(self):
        binary = os.path.join(OLLAMA_DIR, "bin", "ollama")
        if not os.path.exists(binary):
            raise SystemExit("Ollama is not installed: run `python scripts/setup.py --ollama` "
                             "(or the Downloads page), or set KE_OLLAMA_URL to a running server")
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        env = {**os.environ, "OLLAMA_HOST": f"127.0.0.1:{port}", "OLLAMA_MODELS": os.path.join(OLLAMA_DIR, "models"),
               "OLLAMA_NUM_PARALLEL": "8", "OLLAMA_KEEP_ALIVE": "-1", "OLLAMA_LOAD_TIMEOUT": "15m"}
        os.makedirs(os.path.join(OLLAMA_DIR, "logs"), exist_ok=True)
        # Kept after the run: when Ollama fails, the reason is in here.
        self.log = open(os.path.join(OLLAMA_DIR, "logs", f"serve-{os.environ.get('SLURM_JOB_ID', os.getpid())}.log"), "w")
        self.process = subprocess.Popen([binary, "serve"], env=env, stdout=self.log, stderr=subprocess.STDOUT)
        atexit.register(self.stop)
        for _ in range(120):
            try:
                urllib.request.urlopen(self.url + "/api/version", timeout=2)
                return
            except (urllib.error.URLError, OSError):
                time.sleep(1)
        raise RuntimeError(f"ollama serve did not start; see {self.log.name}")

    def stop(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.log.close()


# Ollama sizes its runner's threads to the whole node (64 of 128 cores here),
# while a SLURM job gets a couple of CPUs: oversubscribed, it took longer to
# load a 4B model than Ollama waits. Use the CPUs this process may run on.
THREADS = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)


def ollama_judge(model, url=None):
    loading = time.time()
    url = url or OllamaServer().url
    # Pulled once into external/ollama/models; a no-op when already there.
    _post(url + "/api/pull", {"model": model, "stream": False}, timeout=3600)
    # Load the model now, so its loading is not counted as the first calls' time.
    _post(url + "/api/generate", {"model": model, "prompt": "", "keep_alive": -1,
                                  "options": {"num_thread": THREADS}}, timeout=1800)
    load_seconds = round(time.time() - loading, 1)

    def ask(text):
        reply = _post(url + "/api/chat", {
            "model": model, "stream": False, "think": False, "format": "json",
            "options": {"temperature": 0, "num_predict": 80, "num_thread": THREADS},
            "messages": [{"role": "user", "content": text}]}, timeout=300)
        return reply["message"]["content"]
    judge = Judge(ask, f"ollama:{model}")
    judge.load_seconds = load_seconds
    return judge


def api_judge(model=""):
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "experiments", "run_experiment"))
    import evaluation_config
    from openai import OpenAI
    cfg = evaluation_config.settings()
    if not evaluation_config.judge_configured(cfg):
        raise SystemExit("--judge api needs a key in experiments/run_experiment/evaluation.local.json "
                         "or KE_JUDGE_API_KEY")
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"], timeout=120)
    name = model or cfg["judge_model"]

    def ask(text):
        response = client.chat.completions.create(model=name, temperature=0, max_tokens=80,
                                                  messages=[{"role": "user", "content": text}])
        return response.choices[0].message.content or ""
    return Judge(ask, f"api:{name}")


def make_judge(args, kind=None, model=None):
    kind = kind or getattr(args, "judge", "none")
    if kind == "none":
        return None
    model = model or (args.judge_model if kind == getattr(args, "judge", None) else "") or DEFAULT_JUDGE_MODELS[kind]
    if kind == "local":
        return LocalJudge(model, "cuda:0" if torch.cuda.is_available() else "cpu")
    if kind == "ollama":
        return ollama_judge(model, os.environ.get("KE_OLLAMA_URL"))
    return api_judge(model)
