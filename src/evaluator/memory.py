"""Episodic memory substrates for ENSS agents (Phase-17 corrected schema).

Memory genes and their REAL mechanisms:

- recency:   select the most recent k entries of the experience bank
- retrieval: TF-IDF similarity top-k over the experience bank
- mamba2:    real Mamba-2 substrate (models/mamba_memory.py) processes the
             bank as an ordered sequence; recall scores candidates against
             the resulting order-dependent memory state
- hybrid:    retrieval top-(k-1) plus the most recent entry

Leakage discipline (Phase-17 verification gate): the experience bank comes
ONLY from the benchmark's train/calibration split. Test items are never
stored, so gold test answers can never leak into prompts.

The context_policy gene controls exemplar verbosity:
full / truncated / answer_only.
"""

import hashlib
import math
import re
from collections import Counter

import torch

from models.mamba_memory import MambaMemory

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return _TOKEN_RE.findall(text.lower())


def _stable_token_index(tok, dim):
    """Process-stable token index (Phase-20 hotfix H1).

    Python's built-in hash() is randomized across processes unless
    PYTHONHASHSEED is pinned — embeddings were not reproducible run-to-run.
    SHA-256 gives a fixed mapping in every process.
    """
    digest = hashlib.sha256(tok.encode("utf-8")).hexdigest()
    return int(digest, 16) % dim


def hashed_embedding(text, dim=64):
    """Deterministic bag-of-words hashed embedding (no external model).

    Guaranteed identical across processes (SHA-256 based; regression-tested
    via a two-process subprocess test).
    """
    vec = torch.zeros(dim)
    for tok in tokenize(text):
        vec[_stable_token_index(tok, dim)] += 1.0
    norm = vec.norm()
    return vec / norm if norm > 0 else vec


def tfidf_scores(query, docs):
    """Cosine similarity over TF vectors (pure python, small corpora)."""
    q_counts = Counter(tokenize(query))
    scores = []
    for doc in docs:
        d_counts = Counter(tokenize(doc))
        dot = sum(q_counts[t] * d_counts.get(t, 0) for t in q_counts)
        qn = math.sqrt(sum(v * v for v in q_counts.values())) or 1.0
        dn = math.sqrt(sum(v * v for v in d_counts.values())) or 1.0
        scores.append(dot / (qn * dn))
    return scores


class BaseMemory:
    """Experience-bank memory controller interface."""

    def __init__(self, genome):
        self.genome = genome
        self.bank = []  # list of {"question", "answer"} from TRAIN split

    def store(self, question, answer):
        self.bank.append({"question": question, "answer": answer})

    def recall(self, query, k=3):
        """Return up to k exemplar dicts to inject into the prompt."""
        raise NotImplementedError


class RecencyMemoryController(BaseMemory):
    """Recency: the last k entries of the experience bank."""

    def recall(self, query, k=3):
        return self.bank[-k:]


class RetrievalMemoryController(BaseMemory):
    """Similarity top-k over the whole experience bank.

    retrieval_metric gene (Phase-20): "tfidf" (sparse cosine) or
    "hashed_bow" (cosine over hashed bag-of-words embeddings).
    Note: hashed_bow is NOT a learned dense retriever — the paper-facing
    name stays precise (hotfix H5).
    """

    def __init__(self, genome):
        super().__init__(genome)
        self.metric = getattr(genome, "retrieval_metric", None) or "tfidf"
        self._embeddings = []

    def store(self, question, answer):
        super().store(question, answer)
        if self.metric == "hashed_bow":
            self._embeddings.append(
                hashed_embedding(question + " " + answer, 64))

    def recall(self, query, k=3):
        if not self.bank:
            return []
        if self.metric == "hashed_bow":
            q = hashed_embedding(query, 64)
            scores = [
                torch.cosine_similarity(q, e, dim=0).item()
                for e in self._embeddings
            ]
        else:
            docs = [h["question"] for h in self.bank]
            scores = tfidf_scores(query, docs)
        ranked = sorted(zip(scores, self.bank), key=lambda x: -x[0])
        return [h for s, h in ranked[:k] if s > 0]


class Mamba2MemoryController(BaseMemory):
    """Real Mamba-2 gated recall.

    The substrate processes the experience bank as an ordered embedding
    sequence and produces an order-dependent memory state; candidates are
    scored by cosine similarity between their embedding and that state.
    Substrate parameters are trainable (see evolution/adaptation.py) and
    transferable via evolution/inheritance.py.
    """

    def __init__(self, genome, dim=64):
        super().__init__(genome)
        self.dim = dim
        self.substrate = MambaMemory(hidden_size=dim,
                                     state_size=min(genome.state_size, 64))
        self.embeddings = []
        self._state_cache = None  # invalidated on store / weight change

    def store(self, question, answer):
        super().store(question, answer)
        self.embeddings.append(
            hashed_embedding(question + " " + answer, self.dim))
        self._state_cache = None

    def invalidate_state_cache(self):
        """Must be called after substrate weights change (adaptation,
        inheritance) so the next recall recomputes the memory state."""
        self._state_cache = None

    def memory_state(self):
        """Current order-dependent memory state over the whole bank.

        Cached: the bank is static during evaluation, so the Mamba-2
        forward runs once per bank configuration, not once per query
        (this was a real performance bug caught in the Phase-17 run).
        """
        if not self.embeddings:
            return torch.zeros(self.dim)
        if self._state_cache is None:
            seq = torch.stack(self.embeddings).unsqueeze(0)  # (1, n, dim)
            with torch.no_grad():
                self._state_cache = self.substrate.memory_state(seq).squeeze(0)
        return self._state_cache

    def recall(self, query, k=3):
        if not self.embeddings:
            return []
        state = self.memory_state()
        with torch.no_grad():
            scores = [
                torch.cosine_similarity(state, e, dim=0).item()
                for e in self.embeddings
            ]
        ranked = sorted(zip(scores, self.bank), key=lambda x: -x[0])
        return [h for _, h in ranked[:k]]

    # Trainable-substrate accessors used by adaptation and inheritance.
    def substrate_parameters(self):
        return self.substrate.parameters()

    def substrate_state_dict(self):
        return self.substrate.state_dict()


class HybridMemoryController(BaseMemory):
    """Retrieval + recency mix.

    hybrid_retrieval_fraction gene (Phase-20): fraction of the k slots
    filled by retrieval (rest = most recent). Legacy default (None) keeps
    the Phase-17 behavior: k-1 retrieval + 1 most recent.
    """

    def __init__(self, genome):
        super().__init__(genome)
        self._retrieval = RetrievalMemoryController(genome)
        self.fraction = getattr(genome, "hybrid_fraction", None)

    def store(self, question, answer):
        super().store(question, answer)
        self._retrieval.store(question, answer)

    def recall(self, query, k=3):
        if self.fraction is None:
            picked = self._retrieval.recall(query, k=max(1, k - 1))
            n_recent = 1
        else:
            n_retr = max(0, min(k, round(k * self.fraction)))
            picked = self._retrieval.recall(query, k=n_retr)
            n_recent = k - len(picked)
        for h in reversed(self.bank[-max(0, n_recent):]):
            if all(p is not h for p in picked):
                picked.append(h)
        return picked[:k]


class NoneMemoryController(BaseMemory):
    """Canonical no-memory phenotype (exemplar_count=0): never recalls."""

    def recall(self, query, k=3):
        return []


MEMORY_CONTROLLERS = {
    "none": NoneMemoryController,
    "recency": RecencyMemoryController,
    "retrieval": RetrievalMemoryController,
    "mamba2": Mamba2MemoryController,
    "hybrid": HybridMemoryController,
}


def build_memory_controller(genome):
    """Instantiate the episodic memory substrate named by the genome."""
    cls = MEMORY_CONTROLLERS.get(genome.memory)
    if cls is None:
        raise ValueError("unknown memory substrate: %s" % genome.memory)
    return cls(genome)


# --- context_policy gene: exemplar verbosity + word budget -------------------

def format_exemplar(exemplar, context_policy, exemplar_word_budget=None):
    """Render one experience under the context policy's verbosity budget.

    exemplar_word_budget (Phase-20, active for truncated/answer_only): hard
    cap on exemplar WORDS after mode reduction. Deliberately named "word"
    budget: it counts whitespace words, not model tokens (hotfix token
    semantics rule — no token claim without the model tokenizer).
    """
    answer = exemplar["answer"]
    if context_policy == "full":
        body = answer
    elif context_policy == "truncated":
        body = "\n".join(answer.split("\n")[-2:])
    elif context_policy == "answer_only":
        body = answer.split("\n")[-1]
    else:
        raise ValueError("unknown context policy: %s" % context_policy)
    if exemplar_word_budget:
        words = body.split()
        if len(words) > exemplar_word_budget:
            body = " ".join(words[:exemplar_word_budget])
    return "Question: %s\nAnswer: %s" % (exemplar["question"], body)
