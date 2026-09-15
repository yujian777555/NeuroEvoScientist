"""PubMedQA benchmark adapter for ENSS (Phase-15, Task 3).

Scientific QA (biomedical research questions, yes/no/maybe) — the second
task family used to test task-dependent evolution: GSM8K may favor
reasoning-heavy architectures, PubMedQA may favor memory/retrieval ones.

Same activated-substrate pipeline as GSM8K: episodic memory recall,
reasoning-gene prompt template, compression-gene exemplar budget, real
token-cost measurement, atomic evaluation cache.

Data: pqa_labeled (1000 expert-annotated questions).
Loading order: explicit ``data_path`` -> local cache
``data/pubmedqa/pqal.jsonl`` -> ``datasets`` library -> official GitHub
mirror download.

Cache-format JSONL sample:
    {"question": "<question>\\nContext: <abstract sentences>",
     "answer": "yes|no|maybe"}
"""

import hashlib
import json
import os
import re
import tempfile
import time
import urllib.request

from .memory import build_memory_controller, format_exemplar
from .metrics import compute_metrics

PUBMEDQA_URL = ("https://raw.githubusercontent.com/pubmedqa/pubmedqa/"
                "master/data/ori_pqal.json")

_DEFAULT_CACHE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "pubmedqa"
)

_LABELS = ("yes", "no", "maybe")
_LABEL_RE = re.compile(r"\b(yes|no|maybe)\b", re.IGNORECASE)


def extract_pubmedqa_answer(text):
    """Extract the final yes/no/maybe decision (last mention wins)."""
    matches = _LABEL_RE.findall(text.lower())
    return matches[-1] if matches else None


PROMPT_TEMPLATES = {
    "direct": ("Question: {q}\nAnswer yes, no, or maybe. "
               "End with '#### <yes|no|maybe>'."),
    "verify": ("Question: {q}\nDecide yes/no/maybe, then verify against the "
               "context. End with '#### <yes|no|maybe>'."),
    "planner": ("Question: {q}\nFirst outline what the context says, then "
                "decide. End with '#### <yes|no|maybe>'."),
    "cot": ("Question: {q}\nLet's think step by step. "
            "End with '#### <yes|no|maybe>'."),
}


class PubMedQAEvaluator:
    """Real PubMedQA evaluator; same interface as GSM8KEvaluator."""

    def __init__(self, backend=None, split="test", limit=None,
                 data_path=None, cache_path=None, memory_k=3,
                 disable_memory=False):
        self.backend = backend
        self.split = split
        self.limit = limit
        self.data_path = data_path
        self.cache_path = cache_path
        self.memory_k = memory_k
        self.disable_memory = disable_memory
        self._samples = None
        self._cache = None

    # -- evaluation cache (atomic; crash-safe resume) --------------------------

    def _cache_key(self, genome):
        model = getattr(self.backend, "model_name", "unknown")
        payload = json.dumps({
            "genome": genome.to_dict(), "benchmark": "pubmedqa",
            "limit": self.limit, "model": str(model),
            "pipeline": "substrate-activated-v2",
            "disable_memory": self.disable_memory,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_cache(self):
        if self._cache is None:
            self._cache = {}
            if self.cache_path and os.path.exists(self.cache_path):
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
        return self._cache

    def _store_cache(self, key, metrics):
        if not self.cache_path:
            return
        cache = self._load_cache()
        cache[key] = metrics
        os.makedirs(os.path.dirname(os.path.abspath(self.cache_path)),
                    exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(os.path.abspath(self.cache_path)))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cache, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.cache_path)

    # -- data -----------------------------------------------------------------

    def load_samples(self):
        if self._samples is not None:
            return self._samples

        path = self.data_path or os.path.join(_DEFAULT_CACHE, "pqal.jsonl")
        if not os.path.exists(path):
            self._resolve_dataset(path)

        samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        if self.limit:
            samples = samples[: self.limit]
        self._samples = samples
        return samples

    def _resolve_dataset(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            import datasets
        except ImportError:
            datasets = None

        if datasets is not None:
            ds = datasets.load_dataset("qiaojin/PubMedQA", "pqa_labeled",
                                       split="train")
            with open(path, "w", encoding="utf-8") as f:
                for row in ds:
                    f.write(json.dumps({
                        "question": row["question"] + "\nContext: "
                                    + " ".join(row["context"]["contexts"]),
                        "answer": row["final_decision"],
                    }) + "\n")
            return

        raw_path = path + ".ori.json"
        urllib.request.urlretrieve(PUBMEDQA_URL, raw_path)
        with open(raw_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        with open(path, "w", encoding="utf-8") as f:
            for pmid in sorted(raw):
                row = raw[pmid]
                f.write(json.dumps({
                    "question": row["QUESTION"] + "\nContext: "
                                + " ".join(row["CONTEXTS"]),
                    "answer": row["final_decision"],
                }) + "\n")

    # -- pipeline ---------------------------------------------------------------

    def build_prompt(self, sample, genome, exemplars=None):
        blocks = []
        if exemplars:
            blocks.extend(format_exemplar(e, genome.compression)
                          for e in exemplars)
        template = PROMPT_TEMPLATES.get(genome.reasoning,
                                        PROMPT_TEMPLATES["direct"])
        blocks.append(template.format(q=sample["question"]))
        return "\n\n".join(blocks)

    def _count_tokens(self, prompts):
        tok = getattr(self.backend, "_tokenizer", None)
        if tok is not None:
            return sum(len(tok(p)["input_ids"]) for p in prompts)
        return sum(len(p.split()) for p in prompts)

    def evaluate(self, genome, agent):
        if self.backend is None:
            raise RuntimeError(
                "PubMedQAEvaluator requires an inference backend. "
                "Refusing to fabricate scores; use benchmark='mock' for CI."
            )

        key = self._cache_key(genome)
        cached = self._load_cache().get(key)
        if cached is not None:
            return cached

        samples = self.load_samples()

        memory = None if self.disable_memory else build_memory_controller(genome)
        prompts = []
        for sample in samples:
            exemplars = None if memory is None else memory.recall(
                sample["question"], k=self.memory_k)
            prompts.append(self.build_prompt(sample, genome, exemplars))
            if memory is not None:
                memory.store(sample["question"], sample["answer"])

        start = time.time()
        if hasattr(self.backend, "batch_generate"):
            outputs = self.backend.batch_generate(prompts, genome)
        else:
            outputs = [self.backend(p, genome) for p in prompts]
        latency_sec = time.time() - start

        prompt_tokens = self._count_tokens(prompts)

        task_scores = []
        hard_scores = []  # 'maybe'-gold questions: adaptability proxy
        for sample, output in zip(samples, outputs):
            pred = extract_pubmedqa_answer(output)
            gold = sample["answer"].strip().lower()
            correct = 1.0 if pred == gold else 0.0
            task_scores.append(correct)
            if gold == "maybe":
                hard_scores.append(correct)

        metrics = compute_metrics(agent, task_scores,
                                  shifted_scores=hard_scores or None,
                                  prompt_tokens=prompt_tokens,
                                  n_prompts=len(prompts))
        metrics["latency_sec"] = latency_sec
        metrics["prompt_tokens_total"] = prompt_tokens
        metrics["memory_enabled"] = not self.disable_memory
        self._store_cache(key, metrics)
        return metrics
