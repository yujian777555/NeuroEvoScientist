"""Real episodic memory substrates for ENSS agents (Phase-15, Task 1/2).

Each ``memory`` gene instantiates a controller that manages experience
across one evaluation episode (a benchmark run is a stream of problems).
The controller decides what past experience enters the LLM prompt, so the
memory gene directly changes inference behavior and content:

- attention:  full-context window (keep the most recent K experiences)
- retrieval:  TF-IDF similarity top-k over the episode history
- mamba:      SSM-gated recall — a recurrent hidden state (MambaMemory
              module) integrates hashed experience embeddings; candidates
              are scored by interaction with the current state
- hybrid:     retrieval top-k plus the most recent experience

The ``compression`` gene controls exemplar verbosity (context budget):
none = full solution text, lora = truncated, qlora/int8 = answer only.

Mamba gate weights are untrained placeholders by design; they transfer
parent -> child through evolution/inheritance.py, which is what makes
weight inheritance meaningful once substrates are real.
"""

import math
import re
from collections import Counter

import torch

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return _TOKEN_RE.findall(text.lower())


def hashed_embedding(text, dim=64):
    """Deterministic bag-of-words hashed embedding (no external model)."""
    vec = torch.zeros(dim)
    for tok in tokenize(text):
        vec[hash(tok) % dim] += 1.0
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
    """Episode memory controller interface."""

    def __init__(self, genome):
        self.genome = genome
        self.history = []  # list of (question, answer) dicts

    def store(self, question, answer):
        self.history.append({"question": question, "answer": answer})

    def recall(self, query, k=3):
        """Return up to k exemplar dicts to inject into the prompt."""
        raise NotImplementedError


class AttentionMemoryController(BaseMemory):
    """Full-context: the most recent k experiences (recency window)."""

    def recall(self, query, k=3):
        return self.history[-k:]


class RetrievalMemoryController(BaseMemory):
    """Similarity top-k over the whole episode history."""

    def recall(self, query, k=3):
        if not self.history:
            return []
        docs = [h["question"] for h in self.history]
        scores = tfidf_scores(query, docs)
        ranked = sorted(zip(scores, self.history), key=lambda x: -x[0])
        return [h for s, h in ranked[:k] if s > 0]


class MambaMemoryController(BaseMemory):
    """SSM-gated episodic memory.

    A recurrent state integrates hashed experience embeddings via the
    MambaMemory module; recall scores candidates by cosine similarity
    between their embedding and the current memory state.
    """

    def __init__(self, genome, dim=64):
        super().__init__(genome)
        from models.mamba_memory import MambaMemory
        self.dim = dim
        self.gate = MambaMemory(hidden_size=dim,
                                state_size=min(genome.state_size, dim))
        self.state = torch.zeros(dim)
        self.embeddings = []

    def store(self, question, answer):
        super().store(question, answer)
        emb = hashed_embedding(question + " " + answer, self.dim)
        self.embeddings.append(emb)
        with torch.no_grad():
            self.state = self.gate(emb.unsqueeze(0)).squeeze(0) \
                + 0.9 * self.state

    def recall(self, query, k=3):
        if not self.embeddings:
            return []
        with torch.no_grad():
            scores = [
                torch.cosine_similarity(self.state, e, dim=0).item()
                for e in self.embeddings
            ]
        ranked = sorted(zip(scores, self.history), key=lambda x: -x[0])
        return [h for _, h in ranked[:k]]


class HybridMemoryController(BaseMemory):
    """Retrieval top-k plus the most recent experience."""

    def __init__(self, genome):
        super().__init__(genome)
        self._retrieval = RetrievalMemoryController(genome)

    def store(self, question, answer):
        super().store(question, answer)
        self._retrieval.store(question, answer)

    def recall(self, query, k=3):
        picked = self._retrieval.recall(query, k=max(1, k - 1))
        if self.history:
            latest = self.history[-1]
            if all(h is not latest for h in picked):
                picked = picked + [latest]
        return picked[:k]


MEMORY_CONTROLLERS = {
    "attention": AttentionMemoryController,
    "retrieval": RetrievalMemoryController,
    "mamba": MambaMemoryController,
    "hybrid": HybridMemoryController,
}


def build_memory_controller(genome):
    """Instantiate the episode memory substrate named by the genome."""
    cls = MEMORY_CONTROLLERS.get(genome.memory)
    if cls is None:
        raise ValueError("unknown memory substrate: %s" % genome.memory)
    return cls(genome)


# --- compression gene: exemplar context budget --------------------------------

def format_exemplar(exemplar, compression):
    """Render one experience under the compression gene's context budget."""
    answer = exemplar["answer"]
    if compression == "none":
        body = answer
    elif compression == "lora":
        body = "\n".join(answer.split("\n")[-2:])
    else:  # qlora / int8: most aggressive — final answer only
        body = answer.split("\n")[-1]
    return "Question: %s\nAnswer: %s" % (exemplar["question"], body)
