"""Phase-2 feature contract tests (HashingVectorizer + F0 + shift detector).

Tiny synthetic strings only; no dataset, no encoder download. HashingVectorizer
is stateless, so its output is reproducible; the locked sklearn/numpy versions
are recorded as an advisory contract (not enforced on the local dev box).
"""

import os
import sys

import numpy as np

REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO, "src"))

from phase2 import features  # noqa: E402


def test_contract_pinned_params():
    c = features.feature_contract()
    assert c["n_features"] == 384
    assert c["token_pattern"] == r"(?u)\b\w\w+\b"
    assert c["lowercase"] is True
    assert c["ngram_range"] == [1, 2]
    assert c["alternate_sign"] is False
    assert c["norm"] == "l2"
    assert c["dtype"] == "float64"
    assert c["sklearn_version"] == "1.7.2"
    assert c["numpy_version"] == "2.2.6"
    assert c["f0_dim"] == 2 and c["f1_dim"] == 386


def test_environment_matches_is_advisory_not_blocking():
    status = features.environment_matches()
    assert set(status) >= {"sklearn", "numpy", "required_sklearn",
                           "required_numpy", "ok"}
    assert status["required_sklearn"] == "1.7.2"
    assert isinstance(status["ok"], bool)


def test_normalize_feature_text_truncates():
    assert features.normalize_feature_text("  a   b ") == "a b"
    long = "x" * 3000
    assert len(features.normalize_feature_text(long)) == 2048


def test_f0_exact_values():
    # v6: length = Unicode codepoints; density = numeric / whitespace tokens
    text = "Add 12 and 30 now"
    assert features.whitespace_tokens(text) == ["Add", "12", "and", "30", "now"]
    assert features.question_length(text) == float(len("Add 12 and 30 now"))
    assert features.question_length(text) == 17.0
    assert features.numeric_density(text) == 2.0 / 5.0
    f0 = features.f0_features(text)
    assert f0.dtype == np.float64
    assert list(f0) == [17.0, 0.4]


def test_numeric_token_rule_and_punct_strip():
    assert features.is_numeric_token("48")
    assert features.is_numeric_token("1,000")
    assert features.is_numeric_token("3.5")
    assert features.is_numeric_token("-3")
    assert features.is_numeric_token("48.")     # trailing '.' stripped
    assert not features.is_numeric_token("12:30")  # internal colon not numeric
    assert not features.is_numeric_token("abc")
    assert not features.is_numeric_token("")    # empty never matches
    assert not features.is_numeric_token(".")   # strips to empty
    # empty normalized string -> zero whitespace tokens -> density exactly 0.0
    assert features.whitespace_tokens("   \n  ") == []
    assert features.numeric_density("   ") == 0.0
    # trailing punctuation does not create a numeric token
    assert features.numeric_density("I have 48 apples.") == 0.25


def test_embedding_vector_properties_and_determinism():
    text = "Natalia sold clips to 48 friends in April"
    v1 = features.embedding_vector(text)
    v2 = features.embedding_vector(text, vectorizer=features.build_vectorizer())
    assert v1.shape == (384,) and v1.dtype == np.float64
    # alternate_sign=False -> all non-negative; l2 norm -> unit length
    assert np.all(v1 >= 0.0)
    assert abs(np.linalg.norm(v1) - 1.0) < 1e-9
    # deterministic across separate vectorizer instances (stateless hashing)
    assert np.array_equal(v1, v2)


def test_feature_matrix_dims_and_order():
    texts = ["Add 12 and 30", "hello there world", "one two three four five"]
    m0 = features.feature_matrix(texts, "F0")
    m1 = features.feature_matrix(texts, "F1")
    assert m0.shape == (3, 2) and m1.shape == (3, 386)
    # F1 rows begin with the F0 surface features, in input order
    assert np.allclose(m1[:, :2], m0)
    assert m0.dtype == np.float64 and m1.dtype == np.float64


def test_embedding_hash_and_lock_digest_deterministic():
    texts = ["Natalia sold clips to 48 friends", "What is 2 plus 2?"]
    h1 = features.embedding_hash(texts[0])
    assert h1 == features.embedding_hash(texts[0])     # deterministic
    assert len(h1) == 64
    d1 = features.feature_lock_digest(texts)
    assert d1 == features.feature_lock_digest(texts)   # deterministic
    # order of inputs does not matter (sorted per-item hashes)
    assert d1 == features.feature_lock_digest(list(reversed(texts)))
    # a changed input changes the digest
    assert d1 != features.feature_lock_digest([texts[0], "different"])


def test_shift_detector_fit_and_score():
    rng = np.random.RandomState(0)
    x_fit = rng.randn(20, 3)
    det = features.ShiftDetector(k=5).fit(x_fit)
    in_dist = det.score(x_fit[:3])          # FIT points: small shift
    far = det.score(x_fit.mean(0) + 50.0)   # far away: large shift
    assert in_dist.shape == (3,)
    assert far.shape == (1,)
    assert far[0] > in_dist.max()
    # deterministic
    assert np.array_equal(det.score(x_fit[:3]), in_dist)
