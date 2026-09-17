"""Phase-19 Task 2 gate: dev / holdout / calibration indices are disjoint."""

import os

from evaluator.gsm8k import GSM8KEvaluator
from evaluator.pubmedqa import PubMedQAEvaluator

FIXTURE = os.path.join(os.path.dirname(__file__),
                       "fixtures", "gsm8k_sample.jsonl")
TRAIN_FIXTURE = os.path.join(os.path.dirname(__file__),
                             "fixtures", "gsm8k_train_fixture.jsonl")


def test_gsm8k_start_limit_ranges_disjoint():
    """dev=test[0:100], holdout=test[100:]: index ranges are disjoint by
    construction; verify the slicing semantics directly."""
    ev_dev = GSM8KEvaluator(backend=lambda p, g: "", data_path=FIXTURE,
                            calibration_path=TRAIN_FIXTURE,
                            start=0, limit=1)
    ev_hold = GSM8KEvaluator(backend=lambda p, g: "", data_path=FIXTURE,
                             calibration_path=TRAIN_FIXTURE,
                             start=1, limit=None)
    dev_qs = {s["question"] for s in ev_dev.load_samples()}
    hold_qs = {s["question"] for s in ev_hold.load_samples()}
    assert dev_qs.isdisjoint(hold_qs)
    assert len(ev_dev.load_samples()) == 1
    assert len(ev_hold.load_samples()) == 2  # fixture has 3 items


def test_pubmedqa_holdout_vs_calibration_disjoint():
    """PubMedQA: eval=samples[100:500], calibration=samples[500:]; the offset
    mechanism must keep them disjoint (fixture-clamped here)."""
    fixture = os.path.join(os.path.dirname(__file__),
                           "fixtures", "pubmedqa_sample.jsonl")
    ev = PubMedQAEvaluator(backend=lambda p, g: "", data_path=fixture,
                           calibration_path=fixture, start=0, limit=1)
    eval_qs = {s["question"] for s in ev.load_samples()}
    calib_qs = {s["question"] for s in ev.calibration_samples()}
    assert eval_qs.isdisjoint(calib_qs)


def test_cache_key_separates_ranges(tmp_path):
    """Same genome, different start index -> different cache entries."""
    import json as _json
    cache = str(tmp_path / "c.json")
    from genome.architecture import ArchitectureGenome
    genome = ArchitectureGenome(memory="recency")
    ev0 = GSM8KEvaluator(backend=lambda p, gg: "#### 7", data_path=FIXTURE,
                         calibration_path=TRAIN_FIXTURE, start=0, limit=1,
                         cache_path=cache)
    ev1 = GSM8KEvaluator(backend=lambda p, gg: "#### 7", data_path=FIXTURE,
                         calibration_path=TRAIN_FIXTURE, start=1, limit=1,
                         cache_path=cache)
    ev0.evaluate(genome, agent=None)
    ev1.evaluate(genome, agent=None)
    stored = _json.load(open(cache))
    assert len(stored) == 2


def test_predictions_written(tmp_path):
    pred = str(tmp_path / "preds.jsonl")
    from genome.architecture import ArchitectureGenome
    ev = GSM8KEvaluator(backend=lambda p, g: "#### 7", data_path=FIXTURE,
                        calibration_path=TRAIN_FIXTURE, start=1, limit=2,
                        predictions_path=pred)
    ev.evaluate(ArchitectureGenome(memory="recency"), agent=None)
    import json as _json
    rows = [_json.loads(l) for l in open(pred)]
    assert len(rows) == 2
    assert [r["item_index"] for r in rows] == [1, 2]
    assert all("correct" in r for r in rows)
