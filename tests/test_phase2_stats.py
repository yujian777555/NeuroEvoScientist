"""Phase-2 statistics tests (utility, bootstrap, mid-rank, McNemar, Pareto,
missing/status). Tiny synthetic vectors only; deterministic seeds."""

import os
import sys

import pytest

REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO, "src"))

from phase2 import stats  # noqa: E402


# --- utility ------------------------------------------------------------------

def test_per_item_utility_lambda_algebra():
    # at lambda=0.1, 1000 extra tokens cost exactly 0.01 utility
    assert stats.per_item_utility(1, 1000, 0) == pytest.approx(0.99)
    assert stats.per_item_utility(1, 0, 0) == pytest.approx(1.0)
    assert stats.per_item_utility(0, 500, 500) == pytest.approx(-0.01)
    assert stats.LAMBDA == 0.1 and stats.TOKEN_SCALE == 10000.0


def test_utility_matrix_from_records():
    recs = [{"B1": {"correct": 1, "prompt_tokens": 0, "completion_tokens": 0},
             "B0": {"correct": 1, "prompt_tokens": 2000, "completion_tokens": 0}}]
    U = stats.utility_matrix(recs)
    assert U == [[pytest.approx(1.0), pytest.approx(0.98)]]


# --- type-7 quantile ------------------------------------------------------------

def test_quantile_type7_matches_linear_interpolation():
    vals = [1.0, 2.0, 3.0, 4.0]
    assert stats.quantile_type7(vals, 0.0) == 1.0
    assert stats.quantile_type7(vals, 1.0) == 4.0
    assert stats.quantile_type7(vals, 0.5) == pytest.approx(2.5)
    assert stats.quantile_type7(vals, 0.25) == pytest.approx(1.75)  # R type-7
    assert stats.quantile_type7([5.0], 0.7) == 5.0


# --- paired bootstrap -----------------------------------------------------------

def test_bootstrap_deterministic_and_positive_contrast_passes():
    diffs = [0.05, 0.10, 0.02, 0.08, 0.06, 0.09]  # candidate better on every item
    lo1, hi1, m1 = stats.paired_bootstrap_ci(diffs, n_resamples=500, seed=123)
    lo2, hi2, m2 = stats.paired_bootstrap_ci(diffs, n_resamples=500, seed=123)
    assert (lo1, hi1) == (lo2, hi2) and m1 == m2  # deterministic given seed
    assert lo1 > 0.0                               # clearly positive -> CI above 0
    ok, lo = stats.bootstrap_pass(diffs, n_resamples=500, seed=123)
    assert ok is True and lo > 0.0


def test_bootstrap_zero_difference_not_significant():
    diffs = [0.0] * 20 + [0.05, -0.05]            # centered near zero
    ok, lo = stats.bootstrap_pass(diffs, n_resamples=500, seed=7)
    assert ok is False and lo <= 0.0


def test_bootstrap_shared_indices_preserve_pairing():
    idx = stats.bootstrap_indices(10, n_resamples=50, seed=99)
    assert len(idx) == 50 and all(len(r) == 10 for r in idx)
    assert idx == stats.bootstrap_indices(10, n_resamples=50, seed=99)


# --- mid-rank percentile ----------------------------------------------------------

def test_midrank_percentile():
    null = [0.1, 0.2, 0.3, 0.4]
    assert stats.midrank_percentile(null, 0.3) == pytest.approx((2 + 0.5) / 4)
    assert stats.midrank_percentile(null, 0.05) == pytest.approx(0.0)
    assert stats.midrank_percentile(null, 0.5) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        stats.midrank_percentile([], 0.3)


# --- exact McNemar ---------------------------------------------------------------

def test_mcnemar_exact():
    out = stats.mcnemar_exact([1, 1, 0, 0], [1, 0, 1, 0])  # one win each side
    assert out["discordant"] == 2 and out["p_exact"] == pytest.approx(1.0)
    one_sided = stats.mcnemar_exact([1, 1, 1, 0], [0, 0, 0, 0])  # 3-0
    assert one_sided["a_wins"] == 3 and one_sided["b_wins"] == 0
    assert one_sided["p_exact"] == pytest.approx(0.25)      # 2 * (1/2)^3
    assert stats.mcnemar_exact([1, 0], [1, 0])["p_exact"] == 1.0  # no discordance


# --- Pareto front ------------------------------------------------------------------

def test_pareto_front_accuracy_token():
    pts = {"cheap_low": (0.5, 100), "exp_high": (0.95, 1000),
           "dominated": (0.5, 500), "cheap_high": (0.9, 200)}
    front = stats.pareto_front(pts)
    # (0.5,500) is dominated by (0.5,100); the rest form the accuracy-token front
    assert "dominated" not in front
    assert set(front) == {"cheap_low", "exp_high", "cheap_high"}


# --- missing / status --------------------------------------------------------------

def _ok_rec():
    return {"B1": {"correct": 0, "prompt_tokens": 10, "completion_tokens": 5,
                   "raw_completion": "#### 0"}}


def test_wrong_answer_is_valid_not_missing():
    complete, missing = stats.outcomes_complete([_ok_rec()], ["B1"])
    assert complete and missing == 0  # correct=0 is a valid outcome


def test_missing_outcome_marks_incomplete_invalid():
    bad = {"B1": {"correct": None, "prompt_tokens": 10, "completion_tokens": 5,
                  "raw_completion": "#### 0"}}
    status, missing = stats.confirmatory_status([_ok_rec(), bad], ["B1"])
    assert status == stats.STATUS_INCOMPLETE_INVALID and missing == 1
    missing_config = [_ok_rec(), {}]
    status2, missing2 = stats.confirmatory_status(missing_config, ["B1"])
    assert status2 == stats.STATUS_INCOMPLETE_INVALID and missing2 == 1


def test_null_gate_inconclusive_below_950():
    assert stats.null_gate_status(949) == stats.STATUS_INCONCLUSIVE_NULL
    assert stats.null_gate_status(950) is None
    assert stats.null_gate_status(1000) is None
    assert stats.MIN_VALID_REPLICATES == 950
