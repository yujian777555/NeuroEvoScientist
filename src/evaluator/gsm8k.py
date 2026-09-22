"""GSM8K benchmark adapter for ENSS (Phase-17 corrected semantics).

Real task scoring pipeline:

    TRAIN-split experience bank (leakage-free)
                     ->  memory substrate recall (memory gene, possibly
                         adapted - see evolution/adaptation.py)
                     ->  prompt (reasoning gene template + context_policy
                         exemplar verbosity)
                     ->  backend (pluggable LLM inference)
                     ->  answer extraction  ->  accuracy metrics

Phase-17 corrections:
- exemplars come ONLY from the train split; test items are never stored
  (no train/test leakage in memory exemplars);
- exemplar verbosity is `context_policy` (full/truncated/answer_only) —
  the legacy compression=lora/qlora naming is gone;
- callers may inject a pre-built (e.g. adapted / weight-inherited) memory
  controller; `substrate_fingerprint` separates such variants in the cache.

The evaluator NEVER fabricates scores: without a configured inference
backend it raises. MockEvaluator remains available for CI smoke tests
only and must not be used for paper results.

Dataset format (openai/grade-school-math):
    {"question": "...", "answer": "reasoning...\n#### 72"}

Data loading order:
    1. explicit ``data_path`` / ``calibration_path``
    2. local cache ``data/gsm8k/{split}.jsonl``
    3. ``datasets`` library (if installed)
    4. download from the official GitHub mirror into the cache
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
from .prompts import reasoning_prompt

GSM8K_URL = ("https://raw.githubusercontent.com/openai/grade-school-math/"
             "master/grade_school_math/data/{split}.jsonl")

_DEFAULT_CACHE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "gsm8k"
)

_ANSWER_MARKER = "####"
_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def extract_gsm8k_answer(text):
    """Extract the final numeric answer from a GSM8K-style output."""
    if _ANSWER_MARKER in text:
        text = text.split(_ANSWER_MARKER)[-1]
    numbers = _NUMBER_RE.findall(text)
    if not numbers:
        return None
    return numbers[-1].replace(",", "").rstrip(".")


def answers_match(pred, gold):
    if pred is None or gold is None:
        return False
    try:
        return abs(float(pred) - float(gold)) < 1e-6
    except ValueError:
        return pred.strip() == gold.strip()


# Reasoning-module-conditioned prompt templates. The genome directly shapes
# how the agent is queried, which is what ENSS searches over.
PROMPT_TEMPLATES = {
    "direct": "Question: {q}\nAnswer with the final number only.",
    "verify": ("Question: {q}\nSolve it, then verify your solution step by "
               "step. End with '#### <number>'."),
    "planner": ("Question: {q}\nFirst write a short solution plan, then "
                "execute it. End with '#### <number>'."),
    "cot": ("Question: {q}\nLet's think step by step. "
            "End with '#### <number>'."),
}


class GSM8KEvaluator:
    """Real GSM8K evaluator with a pluggable inference backend.

    Args:
        backend:   callable(prompt: str, genome) -> str. Required for real
                   evaluation; use ``HFTransformersBackend`` or any custom
                   function.
        split:     evaluation split ("test").
        limit:     cap on number of problems (None = all).
        data_path: explicit evaluation JSONL path, overrides cache/download.
        calibration_path: TRAIN-split JSONL feeding the memory bank
                   (leakage-free exemplars + substrate adaptation).
        calibration_size: how many train samples fill the memory bank.
    """

    def __init__(self, backend=None, split="test", limit=None,
                 data_path=None, cache_path=None, memory_k=3,
                 disable_memory=False, calibration_path=None,
                 calibration_size=48, start=0, predictions_path=None):
        self.backend = backend
        self.split = split
        self.limit = limit
        self.start = start
        self.data_path = data_path
        self.cache_path = cache_path
        self.memory_k = memory_k
        # Phase-16 ablation: disable_memory=True removes the episodic memory
        # substrate entirely ("w/o Memory Substrate"), whatever the genome says.
        self.disable_memory = disable_memory
        self.calibration_path = calibration_path
        self.calibration_size = calibration_size
        # Phase-19: per-item prediction logging for statistical tests.
        self.predictions_path = predictions_path
        self._samples = None
        self._calibration = None
        self._cache = None

    # -- evaluation cache (atomic; crash-safe resume for long GPU runs) -------

    def _cache_key(self, genome, substrate_fingerprint=None):
        model = getattr(self.backend, "model_name", "unknown")
        payload = json.dumps({
            "genome": genome.to_dict(), "split": self.split,
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

    # -- data ---------------------------------------------------------------

    def _load_jsonl(self, path):
        if not os.path.exists(path):
            self._resolve_dataset(path)
        samples = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        return samples

    def load_samples(self):
        if self._samples is None:
            path = self.data_path or os.path.join(_DEFAULT_CACHE,
                                                  "%s.jsonl" % self.split)
            samples = self._load_jsonl(path)
            self._samples = samples[self.start:
                                    self.start + self.limit
                                    if self.limit else None]
        return self._samples

    def calibration_samples(self):
        """TRAIN-split samples for the memory bank / substrate adaptation."""
        if self._calibration is None:
            path = self.calibration_path or os.path.join(
                _DEFAULT_CACHE, "train.jsonl")
            self._calibration = self._load_jsonl(path)
        return self._calibration[: self.calibration_size]

    def _resolve_dataset(self, path):
        try:
            import datasets  # noqa: F401
        except ImportError:
            datasets = None

        split = "train" if "train" in os.path.basename(path) else "test"
        if datasets is not None:
            ds = datasets.load_dataset("openai/gsm8k", "main", split=split)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for row in ds:
                    f.write(json.dumps({"question": row["question"],
                                        "answer": row["answer"]}) + "\n")
            return

        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(GSM8K_URL.format(split=split), path)

    # -- pipeline -------------------------------------------------------------

    def build_prompt(self, sample, genome, exemplars=None):
        """Prompt = (memory exemplars) + reasoning-conditioned question.

        memory gene         -> WHICH bank entries appear
        context_policy gene -> HOW verbosely (mode + token_budget)
        reasoning gene      -> the instruction template (+ depth/passes)
        """
        blocks = []
        if exemplars:
            token_budget = getattr(genome, "token_budget", None)
            blocks.extend(format_exemplar(e, genome.context_policy,
                                          token_budget)
                          for e in exemplars)
        hint = ("Answer with the final number only."
                if genome.reasoning == "direct"
                else "End with '#### <number>'.")
        blocks.append(reasoning_prompt(genome, sample["question"], hint))
        return "\n\n".join(blocks)

    def build_memory_bank(self, genome):
        """A memory controller pre-filled from the TRAIN split (leakage-free)."""
        controller = build_memory_controller(genome)
        for s in self.calibration_samples():
            controller.store(s["question"], s["answer"])
        return controller

    def _count_tokens(self, prompts):
        """Real token count when the backend tokenizer is loaded,
        else a word-count proxy."""
        tok = getattr(self.backend, "_tokenizer", None)
        if tok is not None:
            return sum(len(tok(p)["input_ids"]) for p in prompts)
        return sum(len(p.split()) for p in prompts)

    def evaluate(self, genome, agent, memory_controller=None,
                 substrate_fingerprint=None):
        if self.backend is None:
            raise RuntimeError(
                "GSM8KEvaluator requires an inference backend "
                "(e.g. HFTransformersBackend('mistralai/Mistral-7B-v0.1')). "
                "Refusing to fabricate scores; use benchmark='mock' for CI."
            )

        key = self._cache_key(genome, substrate_fingerprint)
        cached = self._load_cache().get(key)
        if cached is not None:
            return cached

        samples = self.load_samples()

        # Memory: bank comes from the TRAIN split only; test items are
        # never stored (no test-answer leakage into prompts).
        memory = None
        if not self.disable_memory:
            memory = memory_controller or self.build_memory_bank(genome)
        # Phase-20: exemplar_count gene overrides the evaluator default;
        # 0 means memory active but no exemplars injected (real phenotype).
        k = getattr(genome, "exemplar_count", None)
        k = self.memory_k if k is None else k
        prompts = []
        for sample in samples:
            exemplars = None if (memory is None or k == 0) else memory.recall(
                sample["question"], k=k)
            prompts.append(self.build_prompt(sample, genome, exemplars))

        start = time.time()
        if hasattr(self.backend, "batch_generate"):
            outputs = self.backend.batch_generate(prompts, genome)
        else:
            outputs = [self.backend(p, genome) for p in prompts]
        latency_sec = time.time() - start

        prompt_tokens = self._count_tokens(prompts)

        task_scores = []
        long_scores = []  # multi-step problems: adaptability proxy
        for sample, output in zip(samples, outputs):
            pred = extract_gsm8k_answer(output)
            gold = extract_gsm8k_answer(sample["answer"])
            correct = 1.0 if answers_match(pred, gold) else 0.0
            task_scores.append(correct)
            if sample["answer"].count("\n") >= 3:
                long_scores.append(correct)

        metrics = compute_metrics(agent, task_scores,
                                  shifted_scores=long_scores or None,
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
        """Per-item outcomes for paired statistics (Phase-19)."""
        os.makedirs(os.path.dirname(os.path.abspath(self.predictions_path)),
                    exist_ok=True)
        with open(self.predictions_path, "a", encoding="utf-8") as f:
            for i, (sample, correct) in enumerate(zip(samples, task_scores)):
                f.write(json.dumps({
                    "benchmark": "gsm8k",
                    "item_index": self.start + i,
                    "architecture": genome.describe(),
                    "genome": genome.to_dict(),
                    "correct": correct,
                }) + "\n")


# Backends live in evaluator/backends.py (Phase-14); re-exported here so
# existing imports (`from evaluator.gsm8k import HFTransformersBackend`)
# keep working.
from .backends import HFTransformersBackend, QwenBackend  # noqa: E402,F401
