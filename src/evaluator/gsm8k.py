"""GSM8K benchmark adapter for ENSS (Phase-13/15).

Real task scoring pipeline:

    dataset (JSONL)  ->  episodic memory recall (memory gene)
                     ->  prompt (reasoning gene template + compression
                         gene exemplar budget)
                     ->  backend (pluggable LLM inference)
                     ->  answer extraction  ->  accuracy metrics

Since Phase-15 every gene affects real inference: memory selects which
past experiences enter the prompt, compression controls their verbosity
(hence real token cost), reasoning sets the instruction template.

The evaluator NEVER fabricates scores: without a configured inference
backend it raises. MockEvaluator remains available for CI smoke tests
only and must not be used for paper results.

Dataset format (openai/grade-school-math):
    {"question": "...", "answer": "reasoning...\n#### 72"}

Data loading order:
    1. explicit ``data_path``
    2. local cache ``data/gsm8k/{split}.jsonl``
    3. ``datasets`` library (if installed)
    4. download from the official GitHub mirror into the cache
"""

import hashlib
import json
import os
import re
import tempfile
import urllib.request

from .memory import build_memory_controller, format_exemplar
from .metrics import compute_metrics

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
        split:     "test" or "train".
        limit:     cap on number of problems (None = all).
        data_path: explicit JSONL path, overrides cache/download.
    """

    def __init__(self, backend=None, split="test", limit=None,
                 data_path=None, cache_path=None, memory_k=3):
        self.backend = backend
        self.split = split
        self.limit = limit
        self.data_path = data_path
        self.cache_path = cache_path
        self.memory_k = memory_k
        self._samples = None
        self._cache = None

    # -- evaluation cache (atomic; crash-safe resume for long GPU runs) -------

    def _cache_key(self, genome):
        model = getattr(self.backend, "model_name", "unknown")
        payload = json.dumps({
            "genome": genome.to_dict(), "split": self.split,
            "limit": self.limit, "model": str(model),
            "pipeline": "substrate-activated-v2",
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

    def load_samples(self):
        if self._samples is not None:
            return self._samples

        path = self.data_path or os.path.join(_DEFAULT_CACHE,
                                              "%s.jsonl" % self.split)
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
        try:
            import datasets  # noqa: F401
        except ImportError:
            datasets = None

        if datasets is not None:
            ds = datasets.load_dataset("openai/gsm8k", "main",
                                       split=self.split)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for row in ds:
                    f.write(json.dumps({"question": row["question"],
                                        "answer": row["answer"]}) + "\n")
            return

        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(GSM8K_URL.format(split=self.split), path)

    # -- pipeline -------------------------------------------------------------

    def build_prompt(self, sample, genome, exemplars=None):
        """Prompt = (memory exemplars) + reasoning-conditioned question.

        The memory gene controls WHICH past experiences appear; the
        compression gene controls HOW verbosely they are rendered; the
        reasoning gene controls the instruction template.
        """
        blocks = []
        if exemplars:
            blocks.extend(format_exemplar(e, genome.compression)
                          for e in exemplars)
        template = PROMPT_TEMPLATES.get(genome.reasoning,
                                        PROMPT_TEMPLATES["direct"])
        blocks.append(template.format(q=sample["question"]))
        return "\n\n".join(blocks)

    def _count_tokens(self, prompts):
        """Real token count when the backend tokenizer is loaded,
        else a word-count proxy."""
        tok = getattr(self.backend, "_tokenizer", None)
        if tok is not None:
            return sum(len(tok(p)["input_ids"]) for p in prompts)
        return sum(len(p.split()) for p in prompts)

    def evaluate(self, genome, agent):
        if self.backend is None:
            raise RuntimeError(
                "GSM8KEvaluator requires an inference backend "
                "(e.g. HFTransformersBackend('mistralai/Mistral-7B-v0.1')). "
                "Refusing to fabricate scores; use benchmark='mock' for CI."
            )

        key = self._cache_key(genome)
        cached = self._load_cache().get(key)
        if cached is not None:
            return cached

        samples = self.load_samples()

        # Episodic memory: history accumulates GOLD experience as the episode
        # proceeds, so prompts are determined upfront and batched generation
        # stays valid.
        memory = build_memory_controller(genome)
        prompts = []
        for sample in samples:
            exemplars = memory.recall(sample["question"],
                                      k=self.memory_k)
            prompts.append(self.build_prompt(sample, genome, exemplars))
            memory.store(sample["question"], sample["answer"])

        if hasattr(self.backend, "batch_generate"):
            outputs = self.backend.batch_generate(prompts, genome)
        else:
            outputs = [self.backend(p, genome) for p in prompts]

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
        self._store_cache(key, metrics)
        return metrics


# Backends live in evaluator/backends.py (Phase-14); re-exported here so
# existing imports (`from evaluator.gsm8k import HFTransformersBackend`)
# keep working.
from .backends import HFTransformersBackend, QwenBackend  # noqa: E402,F401
