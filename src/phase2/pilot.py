"""Two-stage Phase-2 pilot runner skeleton (protocol v5 section 6).

Stage 1 collects frozen per-config outcomes on FIT_pilot + TUNE_pilot (700
items x 5 configs), then runs the policy/feature selection of section 3.3.
Stage 2 opens LEVAL_pilot (300 items) only when TUNE selects F1; when TUNE
selects F0 the run stops NO-GO_IDENTICAL_TO_SIMPLE-FEAT before any LEVAL
output is generated or inspected.

The heavy inference path reuses ``evaluator.gsm8k.GSM8KEvaluator`` and
``evaluator.backends.QwenBackend``; both are imported lazily inside builders so
importing this module never loads torch/transformers or touches a dataset. All
collection is dependency-injected (`collect_fn`), so tests drive the control
flow with synthetic per-item records and a fake meter/clock — no GPU, no real
data, no fabricated results.

Metering uses NVML via ``nvidia-smi`` every 10 s (raw samples retained), with
GPU-active seconds integrated over samples with utilization > 0. The 55-minute
fail-safe aborts with status INCOMPLETE; 60 minutes is the hard cap. Wall time
is never reported as measured GPU-active time. The model revision is locked.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field

from . import policy
from .preflight import write_json
from .stats import (STATUS_INCOMPLETE, STATUS_INCOMPLETE_INVALID,
                    STATUS_NO_GO_SIMPLE_FEAT, STATUS_PASS, per_item_utility)

# --- Locked model + budget constants -----------------------------------------
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"  # locked (as F2)

FIT_TUNE_ITEMS = 700     # 500 FIT_pilot + 200 TUNE_pilot
LEVAL_ITEMS = 300        # LEVAL_pilot
N_CONFIGS = 5
ABORT_MIN = 55.0         # wall-clock fail-safe
CAP_MIN = 60.0           # hard cap
NVML_INTERVAL_SEC = 10.0

STATUS_COMPLETE = "COMPLETE"


def model_lock():
    """The locked model identity recorded in every manifest."""
    return {"model": MODEL_ID, "model_revision": MODEL_REVISION}


def should_abort(elapsed_min, abort_min=ABORT_MIN):
    """55-minute wall-clock fail-safe (GPU inference phase only)."""
    return elapsed_min >= abort_min


def over_cap(elapsed_min, cap_min=CAP_MIN):
    """60-minute hard cap check."""
    return elapsed_min >= cap_min


def leval_authorized(feature_set):
    """LEVAL is opened only when TUNE selects F1 (never to confirm a NO-GO)."""
    return feature_set == "F1"


def _nvidia_smi_sample():
    """One GPU utilization (%) reading via nvidia-smi; used only in real runs."""
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=utilization.gpu",
         "--format=csv,noheader,nounits"]).decode().strip()
    return float(out.splitlines()[0])


class GpuMeter:
    """NVML utilization sampler with raw-sample retention and active seconds.

    ``sample_fn`` (defaults to nvidia-smi) and ``time_fn`` are injectable so
    tests run fully off-GPU. Raw ``(elapsed_sec, util_percent)`` samples are
    kept for the manifest.
    """

    def __init__(self, interval_sec=NVML_INTERVAL_SEC, sample_fn=None,
                 time_fn=time.monotonic):
        self.interval_sec = float(interval_sec)
        self.sample_fn = sample_fn or _nvidia_smi_sample
        self.time_fn = time_fn
        self.samples = []
        self._t0 = None

    def start(self):
        self._t0 = self.time_fn()
        self._t_end = None
        return self

    def stop(self):
        """Freeze the final sample boundary (no open-ended trailing interval)."""
        if self._t_end is None:
            self._t_end = self.time_fn()
        return self

    def record(self, util_percent):
        elapsed = (self.time_fn() - self._t0) if self._t0 is not None else 0.0
        self.samples.append((elapsed, float(util_percent)))

    def poll_once(self):
        self.record(self.sample_fn())

    def active_seconds(self):
        """Integrate GPU-active seconds over samples with utilization > 0.

        Each sample covers the span until the next sample. The final span is
        capped by ``stop()`` rather than an open-ended full interval. This is
        measured GPU-active time, distinct from wall time.
        """
        active = 0.0
        final_elapsed = ((self._t_end - self._t0)
                         if self._t_end is not None else None)
        for i, (elapsed, util) in enumerate(self.samples):
            if util <= 0.0:
                continue
            if i + 1 < len(self.samples):
                span = self.samples[i + 1][0] - elapsed
            elif final_elapsed is not None:
                span = max(0.0, final_elapsed - elapsed)
            else:
                span = self.interval_sec
            active += span
        return active


def item_record(item_id, config, prompt, completion, correct, prompt_tokens,
                completion_tokens, valid, wall_time_sec):
    """The frozen per-item outcome record (section 2)."""
    return {"item_id": item_id, "config": config, "prompt": prompt,
            "completion": completion, "correct": correct,
            "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
            "raw_completion": completion, "valid": bool(valid),
            "wall_time_sec": float(wall_time_sec)}


@dataclass
class PilotResult:
    status: str
    feature_set: str = None
    stage1_records: list = field(default_factory=list)
    leval_records: list = field(default_factory=list)
    gpu_active_seconds: float = 0.0
    wall_time_sec: float = 0.0
    selection: object = None
    manifest: dict = field(default_factory=dict)


def build_backend(model_id=MODEL_ID, device=0, batch_size=32):
    """Real Qwen backend (lazy import; never constructed at module import)."""
    from evaluator.backends import QwenBackend  # noqa: local lazy import
    return QwenBackend(model_id, device=device, batch_size=batch_size)


def build_evaluator(backend, data_path, calibration_path, cache_path,
                    predictions_path):
    """Real GSM8K evaluator wired for per-item prediction logging (lazy)."""
    from evaluator.gsm8k import GSM8KEvaluator  # noqa: local lazy import
    return GSM8KEvaluator(backend=backend, data_path=data_path,
                          calibration_path=calibration_path,
                          cache_path=cache_path, predictions_path=predictions_path)


def run_two_stage(configs, fit_tune_ids, leval_ids, select_fn, collect_fn,
                  meter=None, time_fn=time.monotonic, manifest_path=None):
    """Run the gated two-stage pilot with an injected collector and selector.

    ``collect_fn(config, item_ids) -> list[record]`` yields frozen per-item
    outcomes for one configuration on the given items. ``select_fn(stage1)``
    runs policy selection and returns a ``policy.CandidateResult``. LEVAL is
    collected only when selection selects F1. Abort at the 55-minute fail-safe
    yields status INCOMPLETE with no partial averages presented as complete.
    """
    meter = meter or GpuMeter(time_fn=time_fn)
    meter.start()
    t0 = time_fn()
    stage1 = []

    def _elapsed_min():
        return (time_fn() - t0) / 60.0

    # --- Stage 1: FIT + TUNE outcome collection ------------------------------
    for config in configs:
        if should_abort(_elapsed_min()):
            result = PilotResult(status=STATUS_INCOMPLETE, stage1_records=stage1,
                                 gpu_active_seconds=meter.active_seconds(),
                                 wall_time_sec=time_fn() - t0)
            _flush(manifest_path, result, meter)
            return result
        stage1.extend(collect_fn(config, fit_tune_ids))

    # --- Policy / feature selection ------------------------------------------
    selection = select_fn(stage1)
    if selection is None or selection.status == STATUS_INCOMPLETE_INVALID:
        result = PilotResult(status=STATUS_INCOMPLETE_INVALID,
                             stage1_records=stage1, selection=selection,
                             gpu_active_seconds=meter.active_seconds(),
                             wall_time_sec=time_fn() - t0)
        _flush(manifest_path, result, meter)
        return result
    if not leval_authorized(selection.feature_set):
        # F0 selected -> NO-GO before any LEVAL output is generated/inspected.
        result = PilotResult(status=STATUS_NO_GO_SIMPLE_FEAT, feature_set="F0",
                             stage1_records=stage1, selection=selection,
                             gpu_active_seconds=meter.active_seconds(),
                             wall_time_sec=time_fn() - t0)
        _flush(manifest_path, result, meter)
        return result

    # --- Stage 2: LEVAL one-time confirmatory collection ---------------------
    leval = []
    for config in configs:
        if should_abort(_elapsed_min()):
            result = PilotResult(status=STATUS_INCOMPLETE, feature_set="F1",
                                 stage1_records=stage1, leval_records=leval,
                                 selection=selection,
                                 gpu_active_seconds=meter.active_seconds(),
                                 wall_time_sec=time_fn() - t0)
            _flush(manifest_path, result, meter)
            return result
        leval.extend(collect_fn(config, leval_ids))

    result = PilotResult(status=STATUS_COMPLETE, feature_set="F1",
                         stage1_records=stage1, leval_records=leval,
                         selection=selection,
                         gpu_active_seconds=meter.active_seconds(),
                         wall_time_sec=time_fn() - t0)
    _flush(manifest_path, result, meter)
    return result


def _flush(manifest_path, result, meter):
    if not manifest_path:
        return
    meter.stop()  # cap the final active-time interval before serializing
    manifest = dict(model_lock())
    manifest.update({
        "status": result.status,
        "feature_set": result.feature_set,
        "wall_time_sec": result.wall_time_sec,
        "gpu_active_seconds": meter.active_seconds(),
        "gpu_active_note": "measured NVML util>0 integration; not wall time",
        "nvml_samples": meter.samples,
        "abort_min": ABORT_MIN, "cap_min": CAP_MIN,
        "n_stage1_records": len(result.stage1_records),
        "n_leval_records": len(result.leval_records),
    })
    result.manifest = manifest
    write_json(manifest, manifest_path)


# Re-export for callers that build utility tables from collected records.
__all__ = ["MODEL_ID", "MODEL_REVISION", "GpuMeter", "PilotResult",
           "build_backend", "build_evaluator", "item_record",
           "leval_authorized", "model_lock", "over_cap", "run_two_stage",
           "should_abort", "per_item_utility", "policy"]
