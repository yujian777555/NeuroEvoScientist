"""Frozen feature extraction contract (protocol v5 sections 2/3.1, R5-C).

Feature sets:
- ``F0 = {question length, numeric density}`` (2 dims).
- ``F1 = F0 + frozen query embedding`` (2 + 384 = 386 dims).

The frozen query embedding is a ``sklearn.feature_extraction.text.HashingVectorizer``
with a fully pinned, deterministic contract. ``HashingVectorizer`` is stateless
(no fitted vocabulary), so its murmur-hash output is reproducible across runs;
the confirmatory environment pins ``scikit-learn==1.7.2`` and ``numpy==2.2.6``
(recorded in :data:`REQUIRED_SKLEARN_VERSION` / :data:`REQUIRED_NUMPY_VERSION`).

Text normalization for both the embedding and the surface features is Unicode
NFC, strip ends, collapse internal whitespace to one ASCII space, and truncate
to 2048 characters. All feature extraction is fixed before LEVAL and never uses
outcome information.
"""

from __future__ import annotations

import hashlib
import re

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

from .ids import normalize_text

# --- Locked environment contract (R5-C, protocol v6 section 2.3) ------------
ALGORITHM_ID = "hashing-vectorizer-v1"
REQUIRED_SKLEARN_VERSION = "1.7.2"
REQUIRED_NUMPY_VERSION = "2.2.6"
REQUIRED_SCIPY_VERSION = "1.15.3"

# --- Locked HashingVectorizer hyperparameters --------------------------------
TOKEN_PATTERN = r"(?u)\b\w\w+\b"   # word analyzer, tokens of >=2 word chars
NGRAM_RANGE = (1, 2)
N_FEATURES = 384
LOWERCASE = True
ALTERNATE_SIGN = False
NORM = "l2"
TRUNCATE_CHARS = 2048              # 2,048 Unicode codepoints

# Feature-set dimensions: F0 has two surface features; F1 appends the embedding.
F0_DIM = 2
EMBED_DIM = N_FEATURES
F1_DIM = F0_DIM + EMBED_DIM
FEATURE_SETS = ("F0", "F1")

# Numeric token (v6 section 2.2): after stripping leading/trailing ".,;:!?",
# the whitespace token is fully matched by this regex (empty never matches).
_NUMERIC_TOKEN_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
_PUNCT_STRIP = ".,;:!?"

_VECTORIZER = None


def feature_contract():
    """Return the immutable feature/embedding specification (for manifests)."""
    return {
        "algorithm_id": ALGORITHM_ID,
        "embedding_model": "sklearn.feature_extraction.text.HashingVectorizer",
        "sklearn_version": REQUIRED_SKLEARN_VERSION,
        "numpy_version": REQUIRED_NUMPY_VERSION,
        "scipy_version": REQUIRED_SCIPY_VERSION,
        "analyzer": "word",
        "token_pattern": TOKEN_PATTERN,
        "lowercase": LOWERCASE,
        "ngram_range": list(NGRAM_RANGE),
        "n_features": N_FEATURES,
        "alternate_sign": ALTERNATE_SIGN,
        "norm": NORM,
        "dtype": "float64",
        "text_normalization": ("NFC, strip, collapse whitespace, "
                               "truncate 2048 codepoints"),
        "question_length": ("Unicode codepoint count of the normalized string "
                            "(not bytes, not tokenizer tokens)"),
        "numeric_density": ("numeric-token count / whitespace-token count; "
                            "numeric = fullmatch -?\\d[\\d,]*(?:\\.\\d+)? after "
                            "stripping .,;:!? ; exactly 0.0 when 0 tokens"),
        "f0_dim": F0_DIM,
        "f1_dim": F1_DIM,
    }


def environment_matches():
    """Advisory check: does the running environment match the locked contract?

    Returns a dict; ``ok`` is False when the runtime versions differ from the
    pinned confirmatory versions. This is informational and never raises, so
    local development on other versions is still possible.
    """
    import scipy
    import sklearn
    return {
        "sklearn": sklearn.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "required_sklearn": REQUIRED_SKLEARN_VERSION,
        "required_numpy": REQUIRED_NUMPY_VERSION,
        "required_scipy": REQUIRED_SCIPY_VERSION,
        "ok": (sklearn.__version__ == REQUIRED_SKLEARN_VERSION
               and np.__version__ == REQUIRED_NUMPY_VERSION
               and scipy.__version__ == REQUIRED_SCIPY_VERSION),
    }


def build_vectorizer():
    """Construct the pinned HashingVectorizer (stateless, deterministic)."""
    return HashingVectorizer(
        analyzer="word",
        token_pattern=TOKEN_PATTERN,
        lowercase=LOWERCASE,
        ngram_range=NGRAM_RANGE,
        n_features=N_FEATURES,
        alternate_sign=ALTERNATE_SIGN,
        norm=NORM,
        dtype=np.float64,
    )


def get_vectorizer():
    """Shared process-level vectorizer (HashingVectorizer holds no state)."""
    global _VECTORIZER
    if _VECTORIZER is None:
        _VECTORIZER = build_vectorizer()
    return _VECTORIZER


def normalize_feature_text(text):
    """NFC, strip, collapse whitespace, then truncate to 2048 codepoints."""
    return normalize_text(text)[:TRUNCATE_CHARS]


def whitespace_tokens(text):
    """Normalized string split on the single ASCII space (v6 section 2.2).

    The string is already whitespace-collapsed and stripped, so splitting on
    one ASCII space is equivalent to splitting on runs of ASCII whitespace.
    An empty normalized string yields zero tokens.
    """
    norm = normalize_feature_text(text)
    if norm == "":
        return []
    return norm.split(" ")


def is_numeric_token(token):
    """True when the token, stripped of leading/trailing ``.,;:!?``, fully
    matches ``-?\\d[\\d,]*(?:\\.\\d+)?`` (empty stripped string never matches)."""
    stripped = token.strip(_PUNCT_STRIP)
    if stripped == "":
        return False
    return _NUMERIC_TOKEN_RE.fullmatch(stripped) is not None


def question_length(text):
    """Exact question-length feature: number of Unicode codepoints."""
    return float(len(normalize_feature_text(text)))


def numeric_density(text):
    """Numeric-token count / whitespace-token count (0.0 when no tokens)."""
    tokens = whitespace_tokens(text)
    if not tokens:
        return 0.0
    numeric = sum(1 for t in tokens if is_numeric_token(t))
    return float(numeric) / float(len(tokens))


def f0_features(text):
    """The two F0 surface features as a float64 vector [length, density]."""
    return np.array([question_length(text), numeric_density(text)],
                    dtype=np.float64)


def embedding_vector(text, vectorizer=None):
    """The frozen 384-dim HashingVectorizer embedding of one text (float64)."""
    vec = vectorizer or get_vectorizer()
    mat = vec.transform([normalize_feature_text(text)])
    # dense C-contiguous float64 row of shape (384,)
    return np.ascontiguousarray(
        np.asarray(mat.todense(), dtype=np.float64).ravel())


def embedding_hash(text, vectorizer=None):
    """Lowercase hex SHA-256 of the embedding's raw C-contiguous bytes (v6)."""
    return hashlib.sha256(embedding_vector(text, vectorizer).tobytes(order="C")
                          ).hexdigest()


def feature_lock_digest(texts, vectorizer=None):
    """SHA-256 of the sorted per-item embedding hashes (feature-lock digest)."""
    hashes = sorted(embedding_hash(t, vectorizer) for t in texts)
    return hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest()


def feature_vector(text, feature_set, vectorizer=None):
    """Single-item feature vector for F0 (2 dims) or F1 (386 dims)."""
    base = f0_features(text)
    if feature_set == "F0":
        return base
    if feature_set == "F1":
        return np.concatenate([base, embedding_vector(text, vectorizer)])
    raise ValueError("unknown feature set: %r" % feature_set)


def feature_matrix(texts, feature_set, vectorizer=None):
    """(n_items, dim) float64 feature matrix; rows follow ``texts`` order."""
    rows = [feature_vector(t, feature_set, vectorizer) for t in texts]
    if not rows:
        dim = F0_DIM if feature_set == "F0" else F1_DIM
        return np.zeros((0, dim), dtype=np.float64)
    return np.vstack(rows).astype(np.float64)


class ShiftDetector:
    """Standardized-feature k-NN distance shift gate (protocol section 3.1).

    Each feature dimension is standardized with FIT_pilot mean/std, then the
    shift score is the mean Euclidean distance to the ``k`` nearest FIT_pilot
    items in that space. Fitted once on FIT and frozen; uses no outcomes.
    """

    def __init__(self, k=10):
        self.k = int(k)
        self.mean = None
        self.std = None
        self._z_fit = None

    def fit(self, x_fit):
        x_fit = np.asarray(x_fit, dtype=np.float64)
        self.mean = x_fit.mean(axis=0)
        std = x_fit.std(axis=0)
        std = np.where(std == 0.0, 1.0, std)  # degenerate dims: no scaling
        self.std = std
        self._z_fit = (x_fit - self.mean) / self.std
        return self

    def score(self, x):
        if self._z_fit is None:
            raise RuntimeError("ShiftDetector.score before fit")
        x = np.atleast_2d(np.asarray(x, dtype=np.float64))
        z = (x - self.mean) / self.std
        k = min(self.k, len(self._z_fit))
        out = np.empty(len(z), dtype=np.float64)
        for i, row in enumerate(z):
            d = np.sqrt(((self._z_fit - row) ** 2).sum(axis=1))
            out[i] = np.sort(d)[:k].mean()
        return out
