"""Phase-2 permutation-null tests: deterministic Fisher-Yates streams,
independence, outcome perm, conditional counts, checkpoint, smoke. Synthetic."""

import json
import os
import sys

import pytest

REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO, "src"))

from phase2 import permutation as PM  # noqa: E402
from phase2 import stats  # noqa: E402


def test_stream_seed_namespaced_and_deterministic():
    a = PM.stream_seed(PM.NS_SHUFFLE_FIT, 1)
    assert isinstance(a, int) and 0 <= a < (1 << 64)   # 64-bit unsigned seed
    assert a == PM.stream_seed(PM.NS_SHUFFLE_FIT, 1)
    assert a != PM.stream_seed(PM.NS_SHUFFLE_TUNE, 1)      # namespace separates
    assert a != PM.stream_seed(PM.NS_SHUFFLE_FIT, 2)       # replicate separates


def test_stream_generator_in_range_and_deterministic():
    gen = PM.stream_generator(PM.NS_SHUFFLE_FIT, 1)
    vals = [int(gen.integers(0, 10)) for _ in range(200)]
    assert all(0 <= v <= 9 for v in vals)
    gen2 = PM.stream_generator(PM.NS_SHUFFLE_FIT, 1)       # fresh, same seed
    assert [int(gen2.integers(0, 10)) for _ in range(200)] == vals
    assert int(PM.stream_generator(PM.NS_SHUFFLE_FIT, 1).integers(0, 1)) == 0


def test_deterministic_permutation_valid_and_repeatable():
    p1 = PM.deterministic_permutation(30, PM.NS_SHUFFLE_FIT, 1)
    assert sorted(p1) == list(range(30))                   # a true permutation
    assert p1 == PM.deterministic_permutation(30, PM.NS_SHUFFLE_FIT, 1)


def test_streams_are_independent():
    fit = PM.deterministic_permutation(40, PM.NS_SHUFFLE_FIT, 7)
    tune = PM.deterministic_permutation(40, PM.NS_SHUFFLE_TUNE, 7)
    rand = PM.deterministic_permutation(40, PM.NS_RANDOM_POLICY, 7)
    assert fit != tune          # namespaced FIT/TUNE streams differ
    assert fit != rand          # random-policy stream independent
    other_r = PM.deterministic_permutation(40, PM.NS_SHUFFLE_FIT, 8)
    assert fit != other_r       # different replicate -> different permutation


def test_permute_outcome_table_preserves_within_item_pairing():
    U = [[0.0, 0.1], [1.0, 1.1], [2.0, 2.1], [3.0, 3.1]]
    tok = [[10, 11], [20, 21], [30, 31], [40, 41]]
    perm = PM.deterministic_permutation(4, PM.NS_SHUFFLE_FIT, 3)
    Up, tokp = PM.permute_outcome_table(U, tok, perm)
    for i in range(4):
        src = perm[i]
        assert Up[i] == U[src]          # whole outcome vector moved together
        assert tokp[i] == tok[src]
        # within-item config offset preserved (pairing not broken)
        assert abs((Up[i][1] - Up[i][0]) - (U[src][1] - U[src][0])) < 1e-9


def test_shuffle_pass_gate_thresholds():
    null = [0.01 * i for i in range(1000)]       # 1000 valid replicates
    gate, pct, m = PM.shuffle_pass(null, 1000.0)  # candidate above all
    assert gate is None and pct == pytest.approx(1.0) and m == 1000
    gate_low, _, _ = PM.shuffle_pass(null, 0.0)   # candidate at bottom
    assert gate_low == "FAIL"
    small = [0.01 * i for i in range(949)]        # M < 950 -> INCONCLUSIVE
    gate_inc, pct_inc, m_inc = PM.shuffle_pass(small, 1000.0)
    assert gate_inc == stats.STATUS_INCONCLUSIVE_NULL
    assert pct_inc is None and m_inc == 949


class _Replay:
    """Synthetic replay_fn: F1 on odd replicates (utility=r), F0 NO-GO on even."""

    def __init__(self, n_fit, n_tune):
        self.n_fit = n_fit
        self.n_tune = n_tune
        self.seen = []

    def __call__(self, perm_fit, perm_tune, r):
        # replay receives valid permutations of the right sizes
        assert sorted(perm_fit) == list(range(self.n_fit))
        assert sorted(perm_tune) == list(range(self.n_tune))
        self.seen.append((tuple(perm_fit), tuple(perm_tune), r))
        if r % 2 == 0:
            return {"feature_set": "F0"}             # NO-GO, unscored
        return {"feature_set": "F1", "leval_utility": float(r)}


def test_run_shuffle_null_smoke_counts_and_determinism(tmp_path):
    replay = _Replay(n_fit=6, n_tune=4)
    out = PM.run_shuffle_null(replay, s0=stats.S0, smoke=PM.SMOKE_REPLICATES)
    assert out["smoke"] is True and out["complete"] is False
    # smoke=2 -> replicates r=1 (F1) and r=2 (F0)
    assert out["counts"]["total"] == 2
    assert out["counts"]["valid"] == 1
    assert out["counts"]["f0_nogo"] == 1
    assert out["counts"]["invalid"] == 0
    assert out["null_utilities"] == [1.0]
    assert out["M"] == 1
    assert out["gate"] == stats.STATUS_INCONCLUSIVE_NULL   # M<950 never PASS
    # deterministic: a second run reproduces the same permutations
    replay2 = _Replay(n_fit=6, n_tune=4)
    PM.run_shuffle_null(replay2, s0=stats.S0, smoke=PM.SMOKE_REPLICATES)
    assert replay.seen == replay2.seen


def test_run_shuffle_null_checkpoint_written(tmp_path):
    replay = _Replay(n_fit=5, n_tune=3)
    ckpt = str(tmp_path / "ckpt.json")
    PM.run_shuffle_null(replay, s0=1, smoke=2,
                        checkpoint_path=ckpt, checkpoint_every=1)
    data = json.load(open(ckpt, encoding="utf-8"))
    assert data["replicates_done"] == 2
    assert data["replicates_total"] == 2
    assert data["valid"] == 1 and data["f0_nogo"] == 1
    assert data["complete"] is False and data["smoke"] is True


def test_run_shuffle_null_full_marks_complete():
    replay = _Replay(n_fit=3, n_tune=2)
    out = PM.run_shuffle_null(replay, s0=5, n_replicates=PM.N_REPLICATES)
    assert out["counts"]["total"] == 1000
    assert out["complete"] is True and out["smoke"] is False
    # half F1 (odd r) -> 500 valid; M<950 -> INCONCLUSIVE_NULL
    assert out["M"] == 500
    assert out["gate"] == stats.STATUS_INCONCLUSIVE_NULL
