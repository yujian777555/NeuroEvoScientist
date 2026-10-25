"""Phase-2 pilot runner tests: stage gating, abort/cap, NVML metering, records,
model lock. Fully off-GPU via injected collector/selector and a fake clock."""

import os
import sys

REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO, "src"))

from phase2 import pilot, policy, stats  # noqa: E402

CONFIGS = list(policy.CONFIG_ORDER)
FIT_TUNE_IDS = ["q:%064x" % i for i in range(7)]   # symbolic FIT+TUNE items
LEVAL_IDS = ["q:%064x" % i for i in range(100, 103)]  # symbolic LEVAL items


class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def _collect(clock, step_min):
    def collect(config, item_ids):
        recs = [pilot.item_record(i, config, "prompt", "#### 1", 1, 10, 5,
                                  True, 0.1) for i in item_ids]
        clock.t += step_min * 60.0
        return recs
    return collect


def _select(feature_set):
    def select(stage1):
        return policy.CandidateResult(status=stats.STATUS_PASS,
                                      feature_set=feature_set)
    return select


def test_model_lock_and_thresholds():
    assert pilot.model_lock() == {"model": "Qwen/Qwen2.5-1.5B-Instruct",
                                  "model_revision":
                                  "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"}
    assert pilot.should_abort(54.9) is False
    assert pilot.should_abort(55.0) is True
    assert pilot.over_cap(59.9) is False and pilot.over_cap(60.0) is True
    assert pilot.ABORT_MIN == 55.0 and pilot.CAP_MIN == 60.0
    assert pilot.FIT_TUNE_ITEMS == 700 and pilot.LEVAL_ITEMS == 300


def test_leval_authorized_only_for_f1():
    assert pilot.leval_authorized("F1") is True
    assert pilot.leval_authorized("F0") is False
    assert pilot.leval_authorized(None) is False


def test_item_record_schema():
    rec = pilot.item_record("q:abc", "B1", "p", "#### 2", 1, 12, 7, True, 0.25)
    for key in ("item_id", "config", "prompt", "completion", "correct",
                    "prompt_tokens", "completion_tokens", "raw_completion",
                    "valid", "wall_time_sec"):
        assert key in rec
    assert rec["valid"] is True and rec["correct"] == 1


def test_gpu_meter_active_seconds_integrates_util_positive():
    clock = _Clock()
    meter = pilot.GpuMeter(interval_sec=10.0, sample_fn=lambda: 0.0,
                           time_fn=clock)
    meter.start()                       # t0 = 0
    clock.t = 0.0
    meter.record(50.0)                  # active, spans [0,10)
    clock.t = 10.0
    meter.record(0.0)                   # idle, spans [10,20)
    clock.t = 20.0
    meter.record(80.0)                  # active, last sample spans one interval
    assert meter.active_seconds() == 20.0
    assert len(meter.samples) == 3      # raw samples retained


def test_run_two_stage_nogo_skips_leval():
    clock = _Clock()
    result = pilot.run_two_stage(CONFIGS, FIT_TUNE_IDS, LEVAL_IDS,
                                 _select("F0"), _collect(clock, 1.0),
                                 time_fn=clock)
    assert result.status == stats.STATUS_NO_GO_SIMPLE_FEAT
    assert result.feature_set == "F0"
    assert len(result.stage1_records) == len(CONFIGS) * len(FIT_TUNE_IDS)
    assert result.leval_records == []   # LEVAL never opened on a NO-GO


def test_run_two_stage_f1_collects_leval():
    clock = _Clock()
    result = pilot.run_two_stage(CONFIGS, FIT_TUNE_IDS, LEVAL_IDS,
                                 _select("F1"), _collect(clock, 1.0),
                                 time_fn=clock)
    assert result.status == pilot.STATUS_COMPLETE
    assert result.feature_set == "F1"
    assert len(result.leval_records) == len(CONFIGS) * len(LEVAL_IDS)


def test_run_two_stage_abort_marks_incomplete_no_partial_pass():
    clock = _Clock()
    # 11 min per collect: stage 1 finishes at 55 min, stage 2 aborts at once
    result = pilot.run_two_stage(CONFIGS, FIT_TUNE_IDS, LEVAL_IDS,
                                 _select("F1"), _collect(clock, 11.0),
                                 time_fn=clock)
    assert result.status == stats.STATUS_INCOMPLETE
    assert result.leval_records == []   # no partial LEVAL averages presented
