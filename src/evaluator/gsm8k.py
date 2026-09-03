"""GSM8K benchmark adapter for ENSS (Phase-13, Task 1).

Real task scoring pipeline:

    dataset (JSONL)  ->  prompt (conditioned on genome reasoning module)
                     ->  backend (pluggable LLM inference)
                     ->  answer extraction  ->  accuracy metrics

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

import json
import os
import re
import urllib.request

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
                 data_path=None):
        self.backend = backend
        self.split = split
        self.limit = limit
        self.data_path = data_path
        self._samples = None

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

    def build_prompt(self, sample, genome):
        template = PROMPT_TEMPLATES.get(genome.reasoning,
                                        PROMPT_TEMPLATES["direct"])
        return template.format(q=sample["question"])

    def evaluate(self, genome, agent):
        if self.backend is None:
            raise RuntimeError(
                "GSM8KEvaluator requires an inference backend "
                "(e.g. HFTransformersBackend('mistralai/Mistral-7B-v0.1')). "
                "Refusing to fabricate scores; use benchmark='mock' for CI."
            )

        samples = self.load_samples()
        task_scores = []
        long_scores = []  # multi-step problems: adaptability proxy
        for sample in samples:
            prompt = self.build_prompt(sample, genome)
            output = self.backend(prompt, genome)
            pred = extract_gsm8k_answer(output)
            gold = extract_gsm8k_answer(sample["answer"])
            correct = 1.0 if answers_match(pred, gold) else 0.0
            task_scores.append(correct)
            if sample["answer"].count("\n") >= 3:
                long_scores.append(correct)

        return compute_metrics(agent, task_scores,
                               shifted_scores=long_scores or None)


class HFTransformersBackend:
    """Lazy Hugging Face text-generation backend (real inference)."""

    def __init__(self, model_name, max_new_tokens=256, device=-1):
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.device = device
        self._pipe = None

    def _load(self):
        from transformers import pipeline
        self._pipe = pipeline("text-generation", model=self.model_name,
                              device=self.device)

    def __call__(self, prompt, genome):
        if self._pipe is None:
            self._load()
        out = self._pipe(prompt, max_new_tokens=self.max_new_tokens,
                         do_sample=False)
        return out[0]["generated_text"][len(prompt):]
