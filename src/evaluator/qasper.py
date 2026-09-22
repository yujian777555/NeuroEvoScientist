"""QASPER benchmark adapter for ENSS (Phase-20 third task).

Long-context scientific-paper QA (LongBench qasper, 200 items, whole-paper
context ~3k words). Demand profile: long-context evidence integration —
structurally different from GSM8K (short multi-step arithmetic) and
PubMedQA (abstract-level yes/no/maybe).

Splits (pre-registered in docs/phase20_third_task_preregistration.md):
    dev         = items[0:50]
    holdout     = items[50:150]
    calibration = items[150:200]   (memory bank / adaptation; disjoint)

Metric: LongBench official word-level F1 (max over gold answers).
Prediction: the whole generated continuation.

Same guarantees as the other evaluators: leakage-free calibration bank,
genome-conditioned prompts, token-cost measurement, atomic cache,
per-item prediction logging.
"""

import hashlib
import json
import os
import re
import tempfile
import time
from collections import Counter

from .memory import build_memory_controller, format_exemplar
from .metrics import compute_metrics
from .prompts import reasoning_prompt

_DEFAULT_CACHE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "qasper"
)

_CAL_OFFSET = 150  # calibration = items[150:]; eval slices live below 150

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def qa_f1(prediction, gold):
    """LongBench official QA F1 (word overlap)."""
    p = Counter(_TOKEN_RE.findall(prediction.lower()))
    g = Counter(_TOKEN_RE.findall(gold.lower()))
    if not p or not g:
        return 0.0
    overlap = sum((p & g).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(p.values())
    recall = overlap / sum(g.values())
    return 2 * precision * recall / (precision + recall)


class QasperEvaluator:
    """Real QASPER evaluator; same interface as GSM8KEvaluator."""

    def __init__(self, backend=None, split="test", limit=None,
                 data_path=None, cache_path=None, memory_k=3,
                 disable_memory=False, calibration_path=None,
                 calibration_size=48, start=50, predictions_path=None,
                 max_context_words=2500):
        self.backend = backend
        self.split = split
        self.limit = limit
        self.start = start
        self.data_path = data_path
        self.cache_path = cache_path
        self.memory_k = memory_k
        self.disable_memory = disable_memory
        self.calibration_path = calibration_path
        self.calibration_size = calibration_size
        self.predictions_path = predictions_path
        self.max_context_words = max_context_words
        self._samples = None
        self._calibration = None
        self._cache = None

    # -- cache -----------------------------------------------------------------

    def _cache_key(self, genome, substrate_fingerprint=None):
        model = getattr(self.backend, "model_name", "unknown")
        payload = json.dumps({
            "genome": genome.to_dict(), "benchmark": "qasper",
            "start": self.start, "limit": self.limit, "model": str(model),
            "pipeline": "phase17-v3",
            "disable_memory": self.disable_memory,
            "substrate": substrate_fingerprint or "none",
        }, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _load_cache(self):
        if self._cache is None:
            self._cache = {}
            if self.cache_path and os.path.exists(self.cache_path):
                with open(self.cache_path, encoding="utf-8") as f:
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

    # -- data ------------------------------------------------------------------

    def _load_jsonl(self, path):
        samples = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        return samples

    def load_samples(self):
        if self._samples is None:
            path = self.data_path or os.path.join(_DEFAULT_CACHE,
                                                  "qasper.jsonl")
            samples = self._load_jsonl(path)
            self._samples = samples[self.start:
                                    self.start + self.limit
                                    if self.limit else None]
        return self._samples

    def calibration_samples(self):
        """Calibration slice (items[150:]) disjoint from eval slices,
        normalized to {"question", "answer"} for adaptation/memory use."""
        if self._calibration is None:
            source = self.calibration_path or os.path.join(
                _DEFAULT_CACHE, "qasper.jsonl")
            all_samples = self._load_jsonl(source)
            raw = all_samples[_CAL_OFFSET:]
            self._calibration = [
                {"question": s["input"],
                 "answer": s["answers"][0] if s["answers"] else ""}
                for s in raw
            ]
        return self._calibration[: self.calibration_size]

    # -- pipeline ---------------------------------------------------------------

    def _render_sample(self, sample):
        context = " ".join(sample["context"].split()[: self.max_context_words])
        return context, sample["input"]

    def build_prompt(self, sample, genome, exemplars=None):
        blocks = []
        if exemplars:
            token_budget = getattr(genome, "token_budget", None)
            blocks.extend(format_exemplar(e, genome.context_policy,
                                          token_budget)
                          for e in exemplars)
        context, question = self._render_sample(sample)
        hint = "Answer based on the paper. Be concise. End with '#### <answer>'."
        blocks.append("Paper:\n%s" % context)
        blocks.append(reasoning_prompt(genome, question, hint))
        return "\n\n".join(blocks)

    def build_memory_bank(self, genome):
        controller = build_memory_controller(genome)
        for s in self.calibration_samples():
            controller.store(s["question"], s["answer"])
        return controller

    def _count_tokens(self, prompts):
        tok = getattr(self.backend, "_tokenizer", None)
        if tok is not None:
            return sum(len(tok(p)["input_ids"]) for p in prompts)
        return sum(len(p.split()) for p in prompts)

    def evaluate(self, genome, agent, memory_controller=None,
                 substrate_fingerprint=None):
        if self.backend is None:
            raise RuntimeError(
                "QasperEvaluator requires an inference backend. "
                "Refusing to fabricate scores; use benchmark='mock' for CI."
            )

        key = self._cache_key(genome, substrate_fingerprint)
        cached = self._load_cache().get(key)
        if cached is not None:
            return cached

        samples = self.load_samples()

        memory = None
        if not self.disable_memory:
            memory = memory_controller or self.build_memory_bank(genome)
        k = getattr(genome, "exemplar_count", None)
        k = self.memory_k if k is None else k
        prompts = []
        for sample in samples:
            exemplars = None if (memory is None or k == 0) else memory.recall(
                sample["input"], k=k)
            prompts.append(self.build_prompt(sample, genome, exemplars))

        start = time.time()
        if hasattr(self.backend, "batch_generate"):
            outputs = self.backend.batch_generate(prompts, genome)
        else:
            outputs = [self.backend(p, genome) for p in prompts]
        latency_sec = time.time() - start

        prompt_tokens = self._count_tokens(prompts)

        task_scores = []
        for sample, output in zip(samples, outputs):
            pred = output.split("####")[-1] if "####" in output else output
            best = max((qa_f1(pred, gold) for gold in sample["answers"]),
                       default=0.0)
            task_scores.append(best)

        metrics = compute_metrics(agent, task_scores,
                                  prompt_tokens=prompt_tokens,
                                  n_prompts=len(prompts))
        metrics["latency_sec"] = latency_sec
        metrics["prompt_tokens_total"] = prompt_tokens
        metrics["memory_enabled"] = not self.disable_memory
        if self.predictions_path:
            metrics["item_scores"] = task_scores
            self._write_predictions(samples, task_scores, genome)
        self._store_cache(key, metrics)
        return metrics

    def _write_predictions(self, samples, task_scores, genome):
        os.makedirs(os.path.dirname(os.path.abspath(self.predictions_path)),
                    exist_ok=True)
        with open(self.predictions_path, "a", encoding="utf-8") as f:
            for i, (sample, score) in enumerate(zip(samples, task_scores)):
                f.write(json.dumps({
                    "benchmark": "qasper",
                    "item_index": self.start + i,
                    "architecture": genome.describe(),
                    "genome": genome.to_dict(),
                    "correct": score,
                }) + "\n")
