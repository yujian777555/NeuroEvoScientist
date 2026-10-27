"""Synthetic tests for the high-level Phase-2 runner (no real data/GPU)."""

import json

import numpy as np
import pytest

from phase2 import pilot, policy, runner, stats


def test_record_valid_accepts_wrong_answer_but_not_missing():
    rec = {"valid": True, "correct": 0.0,
           "prompt_tokens": 3, "completion_tokens": 2}
    assert runner._record_valid(rec)
    rec["correct"] = None
    assert not runner._record_valid(rec)
    rec["correct"] = 1.0
    rec["completion_tokens"] = None
    assert not runner._record_valid(rec)


def test_selection_payload_contains_independent_simple_thresholds():
    spec = policy.CandidateSpec("ridge", {"alpha": 1.0}, "ridge|alpha=1")
    sel = policy.Selection(selected=spec, score=0.4)
    result = policy.CandidateResult(
        status=stats.STATUS_PASS, feature_set="F1", delta=0.01, tau=0.2,
        selection=sel, simple_feat={"delta": 0.005, "tau": 0.1},
        best_fixed="B2", majority="B1")
    payload = runner._selection_payload(result)
    assert payload["delta"] == 0.01
    assert payload["simple_feat"]["delta"] == 0.005
    assert payload["best_fixed"] == "B2"


def test_null_checkpoint_counts_actual_done_and_errors(tmp_path):
    payload = runner._null_checkpoint(
        str(tmp_path), 1, 1000, [0.1, 0.2], 3, [{"r": 1, "error": "x"}],
        [0.5, 0.7], 0.0, False, complete=False, done=17,
        forced_status="INCOMPLETE")
    assert payload["counts"] == {"total": 17, "f0_nogo": 3,
                                 "invalid": 1, "valid": 2}
    assert payload["status"] == "INCOMPLETE"
    assert (tmp_path / "analysis" / "null_0001_1000.json").exists()


def test_null_replay_is_conditional_and_has_no_double_invalid(tmp_path):
    calls = []
    def replay(perm_fit, perm_tune, r):
        calls.append((tuple(perm_fit), tuple(perm_tune)))
        if r == 1:
            return {"feature_set": "F0"}
        if r == 2:
            return None
        return {"feature_set": "F1", "leval_utility": 0.25}
    replay.n_fit = 4
    replay.n_tune = 3
    runner._replay_factory = lambda repo, out: replay
    result = runner.run_null("", str(tmp_path), start=1, end=3,
                             smoke=True, timeout_sec=100)
    assert result["counts"] == {"total": 3, "f0_nogo": 1,
                                "invalid": 1, "valid": 1}
    assert result["null_utilities"] == [0.25]
    assert len(calls) == 3
    assert calls[0] != calls[1]  # deterministic but different replicates


def _preliminary(tmp_path, random_pass=True, fixed_pass=True):
    pre = {
        "status": "PENDING_SHUFFLE",
        "summary": {"CANDIDATE": {"utility_mean": 0.5}},
        "contrasts": {
            "BEST-FIXED": {"pass": fixed_pass},
            "MAJORITY": {"pass": True},
            "SIMPLE-FEAT": {"pass": True},
        },
        "random": {"pass": random_pass},
    }
    (tmp_path / "analysis").mkdir(exist_ok=True)
    with open(tmp_path / "analysis" / "stats_preliminary.json", "w", encoding="utf-8") as f:
        json.dump(pre, f)


def _null(tmp_path, utilities, complete=True):
    null = {"counts": {"total": len(utilities), "f0_nogo": 0,
                       "invalid": 0, "valid": len(utilities)},
            "null_utilities": utilities, "complete": complete,
            "cpu_seconds": 2.0, "wall_seconds": 3.0,
            "mean_replicate_seconds": 0.1, "errors": []}
    (tmp_path / "analysis").mkdir(exist_ok=True)
    with open(tmp_path / "analysis" / "null_0001_1000.json", "w", encoding="utf-8") as f:
        json.dump(null, f)


def test_combine_final_all_five_gates_pass(tmp_path):
    _preliminary(tmp_path)
    _null(tmp_path, [0.0] * 950)
    final = runner.combine_final(str(tmp_path))
    assert final["status"] == "PASS"
    assert set(final["gates"]) == {"BEST-FIXED", "MAJORITY", "SIMPLE-FEAT",
                                  "RANDOM", "SHUFFLE"}


def test_combine_final_no_go_when_fixed_fails(tmp_path):
    _preliminary(tmp_path, fixed_pass=False)
    _null(tmp_path, [0.0] * 950)
    assert runner.combine_final(str(tmp_path))["status"] == "NO-GO"


def test_combine_final_inconclusive_when_valid_replicates_insufficient(tmp_path):
    _preliminary(tmp_path)
    _null(tmp_path, [0.0] * 949)
    assert runner.combine_final(str(tmp_path))["status"] == "INCONCLUSIVE_NULL"


def test_combine_final_incomplete_null_cannot_pass(tmp_path):
    _preliminary(tmp_path)
    _null(tmp_path, [0.0] * 950, complete=False)
    assert runner.combine_final(str(tmp_path))["status"] == "INCOMPLETE"


def test_select_frozen_creates_analysis_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "_selection_arrays", lambda out: (
        {}, np.zeros((1, 2)), np.zeros((1, 2)),
        np.ones((1, 5)), np.ones((1, 5)),
        np.ones((1, 5)), np.ones((1, 5)), np.array([0]), {}))
    spec = policy.CandidateSpec("ridge", {"alpha": 1.0}, "ridge|alpha=1")
    result = policy.CandidateResult(
        status=stats.STATUS_NO_GO_SIMPLE_FEAT, feature_set="F0",
        selection=policy.Selection(selected=spec, score=0.0))
    monkeypatch.setattr(runner.policy, "run_candidate_selection", lambda *a: result)
    runner.select_frozen("", str(tmp_path))
    assert (tmp_path / "analysis" / "frozen_selection.json").exists()


def test_merge_null_shards_combines_counts_and_status(tmp_path):
    for r, util in ((1, 0.1), (2, 0.2)):
        payload = {"status": "COMPLETE", "start": r, "end": r,
                   "replicates_done": 1,
                   "counts": {"total": 1, "f0_nogo": 0,
                              "invalid": 0, "valid": 1},
                   "null_utilities": [util], "errors": [],
                   "cpu_seconds": 2.0, "wall_seconds": 3.0 + r,
                   "mean_replicate_seconds": 0.5, "smoke": False,
                   "complete": True, "s0": 20261021}
        (tmp_path / "analysis").mkdir(exist_ok=True)
        with open(tmp_path / "analysis" / ("null_%04d_%04d.json" % (r, r)),
                  "w", encoding="utf-8") as f:
            json.dump(payload, f)
    merged = runner.merge_null_shards(str(tmp_path), shards=[(1, 1), (2, 2)])
    assert merged["counts"] == {"total": 2, "f0_nogo": 0,
                                "invalid": 0, "valid": 2}
    assert merged["null_utilities"] == [0.1, 0.2]
    assert merged["status"] == "COMPLETE"
    assert merged["wall_seconds"] == 5.0
    assert merged["mean_replicate_seconds"] == 0.5
