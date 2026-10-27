"""High-level Phase-2 pilot runner (protocol v6).

Subcommands are exposed through ``src/scripts/phase2_run.py``. This module
contains the real preflight/data-lock, two-stage inference, frozen policy
selection, statistical analysis, and permutation replay logic. No function
in this module fabricates outcomes: every metric is derived from saved raw
records or raises a fail-closed error.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import threading
import time

import numpy as np

from . import features, ids, permutation, pilot, policy, preflight, stats

CONFIG_ORDER = policy.CONFIG_ORDER
CONFIG_INDEX = policy.CONFIG_INDEX
S0 = stats.S0
LAMBDA = stats.LAMBDA
MODEL_LOCK = pilot.model_lock()


def _mkdir(path):
    os.makedirs(path, exist_ok=True)
    return path


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(rows, path):
    _mkdir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _append_jsonl(rows, path):
    _mkdir(os.path.dirname(path))
    with open(path, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _load_inputs(out):
    with open(os.path.join(out, "inputs.json"), encoding="utf-8") as f:
        return json.load(f)


def _load_selection(out):
    with open(os.path.join(out, "analysis", "frozen_selection.json"),
              encoding="utf-8") as f:
        return json.load(f)


def _config_genomes(repo):
    with open(os.path.join(repo, "v2_quality", "fasttrack",
                           "baselines_f1.json"), encoding="utf-8") as f:
        conf = json.load(f)
    from genome.structured import StructuredGenome
    return {name: StructuredGenome(**{**conf["common"],
                                      **conf["baselines"][name]}).normalize()
            for name in CONFIG_ORDER}


# ---------------------------------------------------------------------------
# CPU preflight and immutable locks


def _texts(rows):
    return [r["question"] for r in rows]


def _near_guard_all(names, partitions, inputs, historical):
    checks = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            preflight.exact_overlap_guard(partitions[a], partitions[b], a, b)
            preflight.near_duplicate_guard(inputs[a], inputs[b],
                                             label_a=a, label_b=b)
            checks.append({"a": a, "b": b, "near_duplicates": 0})
    for name, rows in historical:
        other_ids = preflight.canonical_ids(rows)
        preflight.exact_overlap_guard(partitions["BANK"] + partitions["FIT"]
                                      + partitions["TUNE"] + partitions["LEVAL"],
                                      other_ids, label_a="train",
                                      label_b=name)
        preflight.near_duplicate_guard(
            [x for part in names for x in inputs[part]],
            _texts(rows), label_a="train", label_b=name)
        checks.append({"a": "train", "b": name, "near_duplicates": 0})
    return checks


def run_preflight(repo, out):
    """Generate all immutable partition/subset locks and audit manifests."""
    _mkdir(out)
    train_path = os.path.join(repo, "data", "gsm8k", "train.jsonl")
    test_path = os.path.join(repo, "data", "gsm8k", "test.jsonl")
    train = preflight.load_gsm8k_jsonl(train_path)
    test = preflight.load_gsm8k_jsonl(test_path)
    if len(train) != ids.TOTAL_ITEMS:
        raise preflight.PreflightError("GSM8K train count != 7473")
    train_ids = preflight.canonical_ids(train)
    id_to_row = dict(zip(train_ids, train))
    partitions = ids.assign_partitions(train_ids)
    subsets = ids.assign_subsets(partitions)
    ptexts = {name: [id_to_row[nid]["question"] for nid in partitions[name]]
              for name in ids.PARTITION_ORDER}

    svamp_path = os.path.join(repo, "v2_quality", "fasttrack", "data",
                              "svamp_test.json")
    with open(svamp_path, encoding="utf-8") as f:
        svamp_raw = json.load(f)
    svamp = [{"question": str(r["Body"]).strip() + "\n"
              + str(r["Question"]).strip(),
              "answer": str(r["Answer"]), "source_id": r["ID"]}
             for r in svamp_raw]
    checks = _near_guard_all(list(ids.PARTITION_ORDER), partitions, ptexts,
                             [("gsm8k_test", test), ("svamp_f2_locked", svamp)])

    source = {
        "dataset": "openai/gsm8k",
        "split": "train",
        "path": "data/gsm8k/train.jsonl",
        "upstream_url": ("https://raw.githubusercontent.com/openai/"
                         "grade-school-math/master/grade_school_math/data/"
                         "train.jsonl"),
        "immutable_revision": "content-sha256:" + _sha256_file(train_path),
        "train_sha256": _sha256_file(train_path),
        "test_sha256": _sha256_file(test_path),
        "svamp_sha256": _sha256_file(svamp_path),
        "upstream_commit": "not recorded in existing project metadata; content hash is authoritative",
    }
    lock = preflight.build_lock(partitions, subsets, source)
    _mkdir(os.path.join(out, "analysis"))
    preflight.write_json(lock, os.path.join(out, "partition_lock.json"))
    pilot_lock = dict(lock)
    pilot_lock["pilot_subsets"] = lock["subsets"]
    preflight.write_json(pilot_lock, os.path.join(out, "pilot_lock.json"))

    bank_rows = [id_to_row[nid] for nid in partitions["BANK"][:48]]
    stage1_ids = subsets["FIT"] + subsets["TUNE"]
    leval_ids = subsets["LEVAL"]
    _write_jsonl(bank_rows, os.path.join(out, "bank48.jsonl"))
    _write_jsonl([id_to_row[nid] for nid in stage1_ids],
                 os.path.join(out, "stage1.jsonl"))
    _write_jsonl([id_to_row[nid] for nid in leval_ids],
                 os.path.join(out, "leval.jsonl"))
    inputs = {
        "questions": {nid: id_to_row[nid]["question"]
                      for nid in stage1_ids + leval_ids},
        "stage1_ids": stage1_ids,
        "fit_ids": subsets["FIT"],
        "tune_ids": subsets["TUNE"],
        "leval_ids": leval_ids,
        "bank_first48_ids": partitions["BANK"][:48],
    }
    preflight.write_json(inputs, os.path.join(out, "inputs.json"))

    manifest = {
        "status": "PASS",
        "protocol": "phase2-g1-v6",
        "source": source,
        "lock_sha256": {
            "partition_lock.json": _sha256_file(os.path.join(out, "partition_lock.json")),
            "pilot_lock.json": _sha256_file(os.path.join(out, "pilot_lock.json")),
            "inputs.json": _sha256_file(os.path.join(out, "inputs.json")),
            "bank48.jsonl": _sha256_file(os.path.join(out, "bank48.jsonl")),
        },
        "counts": {name: len(partitions[name]) for name in ids.PARTITION_ORDER},
        "pilot_counts": {"FIT": len(subsets["FIT"]),
                         "TUNE": len(subsets["TUNE"]),
                         "LEVAL": len(subsets["LEVAL"])},
        "overlap_checks": checks,
        "bank_first48_ids_sha256": preflight.bank_first48_id_hash(partitions["BANK"]),
        "feature_contract": features.feature_contract(),
        "environment": features.environment_matches(),
        "math500_accessed": False,
        "folds": {nid: ids.assign_fold(nid) for nid in subsets["FIT"]},
    }
    preflight.write_json(manifest, os.path.join(out, "preflight_manifest.json"))
    return manifest


# ---------------------------------------------------------------------------
# Real inference


def _record_valid(rec):
    return (rec.get("valid") is True
            and rec.get("correct") in (0.0, 1.0, 0, 1)
            and isinstance(rec.get("prompt_tokens"), int)
            and isinstance(rec.get("completion_tokens"), int))


def _collect_config(config_name, item_ids, stage, repo, out, backend, genomes):
    """Collect/resume one config; all returned records are raw and auditable."""
    result_dir = os.path.join(out, "results", stage)
    path = os.path.join(result_dir, config_name + ".jsonl")
    existing = {}
    if os.path.exists(path):
        for rec in _read_jsonl(path):
            if _record_valid(rec):
                existing[rec["item_id"]] = rec
    samples = _read_jsonl(os.path.join(out, stage + ".jsonl"))
    if len(samples) != len(item_ids):
        raise RuntimeError("stage input length mismatch")
    genome = genomes[config_name]
    ev = pilot.build_evaluator(
        backend, data_path=os.path.join(out, stage + ".jsonl"),
        calibration_path=os.path.join(out, "bank48.jsonl"),
        cache_path=os.path.join(out, "caches", stage + "_" + config_name + ".json"),
        predictions_path=None)
    memory = ev.build_memory_bank(genome)
    k = getattr(genome, "exemplar_count", None)
    k = ev.memory_k if k is None else k
    pending = [(i, sample) for i, sample in enumerate(samples)
               if item_ids[i] not in existing]
    for batch_start in range(0, len(pending), backend.batch_size):
        batch = pending[batch_start:batch_start + backend.batch_size]
        prompts = []
        for _, sample in batch:
            exemplars = None if memory is None or k == 0 else memory.recall(
                sample["question"], k=k)
            prompts.append(ev.build_prompt(sample, genome, exemplars))
        t0 = time.monotonic()
        try:
            outputs = backend.batch_generate(prompts, genome)
        except Exception as exc:
            outputs = [None] * len(batch)
            error = type(exc).__name__ + ": " + str(exc)
        else:
            error = None
        batch_wall = time.monotonic() - t0
        new_records = []
        for (item_idx, sample), prompt, completion in zip(batch, prompts, outputs):
            valid = isinstance(completion, str) and len(completion) > 0
            pred = __import__("evaluator.gsm8k", fromlist=["extract_gsm8k_answer"]
                              ).extract_gsm8k_answer(completion or "")
            gold = __import__("evaluator.gsm8k", fromlist=["extract_gsm8k_answer"]
                              ).extract_gsm8k_answer(sample["answer"])
            correct = (float(__import__("evaluator.gsm8k",
                                        fromlist=["answers_match"]).answers_match(pred, gold))
                       if valid else None)
            from evaluator.memory import _effective_to_dict
            rec = {
                "item_id": item_ids[item_idx],
                "config": config_name,
                "model": backend.model_name,
                "model_revision": pilot.MODEL_REVISION,
                "genome_sha256": hashlib.sha256(json.dumps(
                    _effective_to_dict(genome, "gsm8k"),
                    sort_keys=True).encode()).hexdigest(),
                "prompt": prompt,
                "completion": completion,
                "raw_completion": completion,
                "correct": correct,
                "prompt_tokens": len(backend._tokenizer(prompt)["input_ids"]),
                "completion_tokens": (len(backend._tokenizer(completion)["input_ids"])
                                      if valid else None),
                "valid": valid and error is None,
                "error": error,
                "batch_index": batch_start // backend.batch_size,
                "batch_wall_time_sec": batch_wall,
            }
            new_records.append(rec)
        _append_jsonl(new_records, path)
        for rec in new_records:
            if _record_valid(rec):
                existing[rec["item_id"]] = rec
    missing = [nid for nid in item_ids if nid not in existing]
    if missing:
        raise RuntimeError("missing/invalid outcomes for %s: %d items"
                           % (config_name, len(missing)))
    return [existing[nid] for nid in item_ids]


def _meter_start():
    meter = pilot.GpuMeter().start()
    stop_event = threading.Event()

    def loop():
        while not stop_event.wait(10.0):
            try:
                meter.poll_once()
            except Exception:
                return

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return meter, stop_event, thread


def _meter_stop(meter, stop_event, thread):
    stop_event.set()
    thread.join(timeout=15)
    meter.stop()
    return meter


def _selection_arrays(out):
    inputs = _load_inputs(out)
    fit_ids = inputs["fit_ids"]
    tune_ids = inputs["tune_ids"]
    questions = inputs["questions"]
    recs = {}
    for cfg in CONFIG_ORDER:
        recs[cfg] = {r["item_id"]: r for r in _read_jsonl(
            os.path.join(out, "results", "stage1", cfg + ".jsonl"))}
    def matrices(item_ids):
        U, T, C, P, K = [], [], [], [], []
        for nid in item_ids:
            ur, tr, cr, pr, kr = [], [], [], [], []
            for cfg in CONFIG_ORDER:
                r = recs[cfg].get(nid)
                if not _record_valid(r):
                    raise RuntimeError("invalid/missing outcome %s %s" % (cfg, nid))
                ur.append(stats.per_item_utility(r["correct"], r["prompt_tokens"],
                                                 r["completion_tokens"]))
                tr.append(r["prompt_tokens"] + r["completion_tokens"])
                cr.append(float(r["correct"]))
                pr.append(r["prompt_tokens"])
                kr.append(r["completion_tokens"])
            U.append(ur); T.append(tr); C.append(cr); P.append(pr); K.append(kr)
        return (np.asarray(U), np.asarray(T), np.asarray(C),
                np.asarray(P), np.asarray(K))
    X_fit = {fs: features.feature_matrix(
        [questions[nid] for nid in fit_ids], fs) for fs in features.FEATURE_SETS}
    X_tune = {fs: features.feature_matrix(
        [questions[nid] for nid in tune_ids], fs) for fs in features.FEATURE_SETS}
    U_fit, tok_fit, _, _, _ = matrices(fit_ids)
    U_tune, tok_tune, _, _, _ = matrices(tune_ids)
    folds = np.asarray(ids.assign_folds(fit_ids))
    return inputs, X_fit, X_tune, U_fit, tok_fit, U_tune, tok_tune, folds, recs


def _selection_payload(result):
    spec = result.selection.selected
    return {
        "status": result.status,
        "feature_set": result.feature_set,
        "selected_model": {"cls": spec.cls, "params": spec.params,
                           "grid_key": spec.grid_key},
        "cv_score": result.selection.score,
        "delta": result.delta,
        "tau": result.tau,
        "simple_feat": result.simple_feat,
        "best_fixed": result.best_fixed,
        "majority": result.majority,
        "lambda": LAMBDA,
        "s0": S0,
    }


def select_frozen(repo, out):
    """Freeze the adaptive policy using only FIT/TUNE outcomes (never LEVAL)."""
    inputs, X_fit, X_tune, U_fit, tok_fit, U_tune, tok_tune, folds, _ = \
        _selection_arrays(out)
    try:
        result = policy.run_candidate_selection(
            X_fit["F0"], X_fit["F1"], folds, U_fit, tok_fit,
            X_tune["F0"], X_tune["F1"], U_tune, tok_tune)
    except Exception as exc:
        result = policy.CandidateResult(status=stats.STATUS_INCOMPLETE_INVALID)
        result.error = str(exc)
    payload = _selection_payload(result) if result.selection is not None else {
        "status": result.status, "error": getattr(result, "error", "selection failed")}
    _mkdir(os.path.join(out, "analysis"))
    preflight.write_json(payload, os.path.join(out, "analysis",
                                                "frozen_selection.json"))
    return result


def run_inference(repo, out, stage):
    """Run one real inference stage on a single visible GPU."""
    inputs = _load_inputs(out)
    item_ids = inputs["stage1_ids"] if stage == "stage1" else inputs["leval_ids"]
    backend = pilot.build_backend(device=0, batch_size=32)
    backend._load()  # model and tokenizer are loaded exactly once per process
    genomes = _config_genomes(repo)
    meter, stop_event, thread = _meter_start()
    started = time.monotonic()
    manifest_path = os.path.join(out, "results", stage, "run_manifest.json")
    _mkdir(os.path.dirname(manifest_path))
    try:
        if stage == "stage1":
            def collect(cfg, ids_):
                # The second call uses the LEVAL file, not stage1.jsonl.
                stage_name = "leval" if ids_ is inputs["leval_ids"] else "stage1"
                return _collect_config(cfg, ids_, stage_name, repo, out,
                                       backend, genomes)
            result = pilot.run_two_stage(
                CONFIG_ORDER, item_ids, inputs["leval_ids"],
                select_fn=lambda _records: select_frozen(repo, out),
                collect_fn=collect,
                meter=meter, manifest_path=manifest_path)
        else:
            selection = _load_selection(out)
            if selection.get("feature_set") != "F1":
                raise RuntimeError("LEVAL inference forbidden without F1 selection")
            leval_records = []
            for cfg in CONFIG_ORDER:
                if pilot.should_abort((time.monotonic() - started) / 60.0):
                    result = pilot.PilotResult(status=stats.STATUS_INCOMPLETE)
                    break
                leval_records.extend(_collect_config(
                    cfg, item_ids, stage, repo, out, backend, genomes))
            else:
                result = pilot.PilotResult(status="COMPLETE",
                                           feature_set="F1",
                                           leval_records=leval_records)
            pilot._flush(manifest_path, result, meter)
    finally:
        _meter_stop(meter, stop_event, thread)
    return result


# ---------------------------------------------------------------------------
# Frozen-policy statistical analysis


def _metrics(U, C, P, K, actions=None):
    if actions is None:
        actions = np.arange(U.shape[1])[None, :].repeat(U.shape[0], axis=0)
    idx = np.arange(U.shape[0])
    return {
        "n_items": int(U.shape[0]),
        "accuracy": float(C[idx, actions].mean()),
        "prompt_tokens_total": int(P[idx, actions].sum()),
        "completion_tokens_total": int(K[idx, actions].sum()),
        "utility_mean": float(U[idx, actions].mean()),
    }


def _policy_metrics(U, C, P, K, action_vector):
    idx = np.arange(U.shape[0])
    return {
        "n_items": int(U.shape[0]),
        "accuracy": float(C[idx, action_vector].mean()),
        "prompt_tokens_total": int(P[idx, action_vector].sum()),
        "completion_tokens_total": int(K[idx, action_vector].sum()),
        "utility_mean": float(U[idx, action_vector].mean()),
    }


def _contrast(name, cand_u, other_u, cand_c, other_c):
    lo, hi, _ = stats.paired_bootstrap_ci(cand_u - other_u, seed=S0)
    return {"name": name, "ci95_lo": lo, "ci95_hi": hi,
            "mean_diff": float(np.mean(cand_u - other_u)),
            "pass": bool(lo > 0.0),
            "mcnemar": stats.mcnemar_exact(cand_c, other_c)}


def run_analysis(repo, out):
    """Score the frozen candidate and all predeclared controls on LEVAL."""
    frozen = _load_selection(out)
    if frozen.get("feature_set") != "F1":
        return {"status": frozen.get("status", "NO-GO")}
    inputs, X_fit, X_tune, U_fit, tok_fit, U_tune, tok_tune, folds, _ = \
        _selection_arrays(out)
    result = policy.run_candidate_selection(
        X_fit["F0"], X_fit["F1"], folds, U_fit, tok_fit,
        X_tune["F0"], X_tune["F1"], U_tune, tok_tune)
    if _selection_payload(result) != frozen:
        raise RuntimeError("deterministic selection does not match frozen_selection.json")

    questions = inputs["questions"]
    leval_ids = inputs["leval_ids"]
    X_leval = {fs: features.feature_matrix(
        [questions[nid] for nid in leval_ids], fs) for fs in features.FEATURE_SETS}
    recs = {cfg: {r["item_id"]: r for r in _read_jsonl(
        os.path.join(out, "results", "leval", cfg + ".jsonl"))}
        for cfg in CONFIG_ORDER}
    U, C, P, K = [], [], [], []
    for nid in leval_ids:
        ur, cr, pr, kr = [], [], [], []
        for cfg in CONFIG_ORDER:
            r = recs[cfg].get(nid)
            if not _record_valid(r):
                raise RuntimeError("incomplete LEVAL outcome %s %s" % (cfg, nid))
            ur.append(stats.per_item_utility(r["correct"], r["prompt_tokens"],
                                             r["completion_tokens"]))
            cr.append(float(r["correct"]))
            pr.append(r["prompt_tokens"])
            kr.append(r["completion_tokens"])
        U.append(ur); C.append(cr); P.append(pr); K.append(kr)
    U, C, P, K = map(np.asarray, (U, C, P, K))
    tokens = P + K

    det_f1 = features.ShiftDetector().fit(X_fit["F1"])
    det_f0 = features.ShiftDetector().fit(X_fit["F0"])
    cand_scores = result.candidate.scores(X_leval["F1"])
    cand_shift = det_f1.score(X_leval["F1"])
    cand_actions = np.asarray([
        policy.choose_action(cand_scores[i], result.delta, cand_shift[i], result.tau)
        for i in range(len(leval_ids))])
    simple_model = policy.final_refit(result.selection.selected, X_fit["F0"],
                                      U_fit, tok_fit)
    simple_scores = simple_model.scores(X_leval["F0"])
    simple_shift = det_f0.score(X_leval["F0"])
    simple_actions = np.asarray([
        policy.choose_action(simple_scores[i], result.simple_feat["delta"],
                             simple_shift[i], result.simple_feat["tau"])
        for i in range(len(leval_ids))])
    fixed_idx = CONFIG_INDEX[result.best_fixed]
    majority_idx = CONFIG_INDEX[result.majority]
    cand_u = U[np.arange(len(U)), cand_actions]
    simple_u = U[np.arange(len(U)), simple_actions]
    cand_c = C[np.arange(len(C)), cand_actions]

    summaries = {cfg: _policy_metrics(U, C, P, K,
                                      np.full(len(U), CONFIG_INDEX[cfg]))
                 for cfg in CONFIG_ORDER}
    summaries["CANDIDATE"] = _policy_metrics(U, C, P, K, cand_actions)
    summaries["SIMPLE-FEAT"] = _policy_metrics(U, C, P, K, simple_actions)
    summaries["BEST-FIXED"] = summaries[result.best_fixed]
    summaries["MAJORITY"] = summaries[result.majority]
    contrasts = {
        "BEST-FIXED": _contrast("BEST-FIXED", cand_u, U[:, fixed_idx],
                                cand_c, C[:, fixed_idx]),
        "MAJORITY": _contrast("MAJORITY", cand_u, U[:, majority_idx],
                              cand_c, C[:, majority_idx]),
        "SIMPLE-FEAT": _contrast("SIMPLE-FEAT", cand_u, simple_u,
                                 cand_c, C[np.arange(len(C)), simple_actions]),
    }
    random_utils = []
    for r in range(1, 1001):
        gen = stats.stream_generator(permutation.NS_RANDOM_POLICY, r, S0)
        actions = gen.integers(0, len(CONFIG_ORDER), size=len(U))
        random_utils.append(float(U[np.arange(len(U)), actions].mean()))
    random_pct = stats.midrank_percentile(random_utils,
                                          summaries["CANDIDATE"]["utility_mean"])
    points = {name: (m["accuracy"],
                     m["prompt_tokens_total"] + m["completion_tokens_total"])
              for name, m in summaries.items()}
    preliminary = {
        "status": "PENDING_SHUFFLE",
        "selection": frozen,
        "summary": summaries,
        "contrasts": contrasts,
        "random": {"n": 1000, "midrank_percentile": random_pct,
                   "pass": bool(random_pct >= stats.MIDRANK_THRESHOLD)},
        "pareto_front": stats.pareto_front(points),
        "candidate_actions": {nid: CONFIG_ORDER[int(a)]
                              for nid, a in zip(leval_ids, cand_actions)},
        "simple_actions": {nid: CONFIG_ORDER[int(a)]
                           for nid, a in zip(leval_ids, simple_actions)},
        "null_random_utilities": random_utils,
    }
    preflight.write_json(preliminary,
                         os.path.join(out, "analysis", "stats_preliminary.json"))
    with open(os.path.join(out, "analysis", "summary.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["system", "n_items", "accuracy",
                                          "prompt_tokens_total",
                                          "completion_tokens_total", "utility_mean"])
        w.writeheader()
        for name, m in summaries.items():
            w.writerow({"system": name, **m})
    return preliminary


# ---------------------------------------------------------------------------
# Adaptive permutation replay


def _replay_factory(repo, out):
    inputs, X_fit, X_tune, U_fit, tok_fit, U_tune, tok_tune, folds, _ = \
        _selection_arrays(out)
    questions = inputs["questions"]
    leval_ids = inputs["leval_ids"]
    X_leval = {fs: features.feature_matrix(
        [questions[nid] for nid in leval_ids], fs) for fs in features.FEATURE_SETS}
    recs = {cfg: {r["item_id"]: r for r in _read_jsonl(
        os.path.join(out, "results", "leval", cfg + ".jsonl"))}
        for cfg in CONFIG_ORDER}
    U = np.asarray([[stats.per_item_utility(recs[cfg][nid]["correct"],
                                             recs[cfg][nid]["prompt_tokens"],
                                             recs[cfg][nid]["completion_tokens"])
                     for cfg in CONFIG_ORDER] for nid in leval_ids])
    C = np.asarray([[float(recs[cfg][nid]["correct"]) for cfg in CONFIG_ORDER]
                    for nid in leval_ids])
    det_f1 = features.ShiftDetector().fit(X_fit["F1"])

    def replay(perm_fit, perm_tune, r):
        result = policy.run_candidate_selection(
            X_fit["F0"], X_fit["F1"], folds, U_fit[perm_fit], tok_fit[perm_fit],
            X_tune["F0"], X_tune["F1"], U_tune[perm_tune], tok_tune[perm_tune])
        if result.status == stats.STATUS_NO_GO_SIMPLE_FEAT:
            return {"feature_set": "F0"}
        if result.status != stats.STATUS_PASS:
            return None
        scores = result.candidate.scores(X_leval["F1"])
        shift = det_f1.score(X_leval["F1"])
        actions = [policy.choose_action(scores[i], result.delta, shift[i], result.tau)
                   for i in range(len(U))]
        return {"feature_set": "F1",
                "leval_utility": float(U[np.arange(len(U)), actions].mean())}
    replay.n_fit = len(U_fit)
    replay.n_tune = len(U_tune)
    return replay


def run_null(repo, out, start=1, end=1000, smoke=False, timeout_sec=14400):
    """Run a deterministic shard of the adaptive SHUFFLE null on CPU only."""
    replay = _replay_factory(repo, out)
    null_utils, f0_nogo, errors = [], 0, []
    times = []
    t0 = time.monotonic()
    target = end - start + 1
    for r in range(start, end + 1):
        tr = time.monotonic()
        perm_fit = permutation.deterministic_permutation(replay.n_fit,
                                                         permutation.NS_SHUFFLE_FIT, r, S0)
        perm_tune = permutation.deterministic_permutation(replay.n_tune,
                                                          permutation.NS_SHUFFLE_TUNE, r, S0)
        error = None
        try:
            ans = replay(perm_fit, perm_tune, r)
        except Exception as exc:
            ans = None
            error = str(exc)
        if ans is None:
            errors.append({"r": r, "error": error or "invalid replicate"})
        elif ans.get("feature_set") == "F0":
            f0_nogo += 1
        else:
            null_utils.append(float(ans["leval_utility"]))
        times.append(time.monotonic() - tr)
        done = r - start + 1
        if done % 10 == 0:
            _null_checkpoint(out, start, end, null_utils, f0_nogo, errors,
                             times, t0, smoke, complete=False, done=done)
        if time.monotonic() - t0 >= timeout_sec:
            return _null_checkpoint(out, start, end, null_utils, f0_nogo, errors,
                                    times, t0, smoke, complete=False, done=done,
                                    forced_status="INCOMPLETE")
    return _null_checkpoint(out, start, end, null_utils, f0_nogo, errors,
                            times, t0, smoke, complete=True, done=target)


def _null_checkpoint(out, start, end, null_utils, f0_nogo, errors, times, t0,
                     smoke, complete, forced_status=None, done=None):
    m = len(null_utils)
    total = (end - start + 1) if done is None else done
    status = forced_status
    if status is None:
        status = "SMOKE" if smoke else ("COMPLETE" if complete else "INCOMPLETE")
    payload = {
        "status": status,
        "start": start, "end": end, "replicates_done": total,
        "counts": {"total": total, "f0_nogo": f0_nogo,
                   "invalid": len(errors), "valid": m},
        "null_utilities": null_utils,
        "errors": errors,
        "cpu_seconds": sum(times),
        "wall_seconds": time.monotonic() - t0,
        "mean_replicate_seconds": float(np.mean(times)) if times else 0.0,
        "smoke": smoke,
        "complete": complete,
        "s0": S0,
    }
    name = "null_smoke.json" if smoke else "null_%04d_%04d.json" % (start, end)
    _mkdir(os.path.join(out, "analysis"))
    preflight.write_json(payload, os.path.join(out, "analysis", name))
    return payload


def merge_null_shards(out, shard_size=25, shards=None):
    """Merge deterministic null shards into the canonical 1..1000 artifact."""
    null_utilities, errors = [], []
    counts = {"total": 0, "f0_nogo": 0, "invalid": 0, "valid": 0}
    cpu_seconds = 0.0
    wall_seconds = 0.0
    weighted_rate = 0.0
    complete = True
    if shards is None:
        shards = [(s, min(1000, s + shard_size - 1))
                  for s in range(1, 1001, shard_size)]
    for start, end in shards:
        path = os.path.join(out, "analysis", "null_%04d_%04d.json" % (start, end))
        if not os.path.exists(path):
            raise FileNotFoundError("missing null shard: " + path)
        with open(path, encoding="utf-8") as f:
            shard = json.load(f)
        null_utilities.extend(shard["null_utilities"])
        errors.extend(shard.get("errors", []))
        for key in counts:
            counts[key] += shard["counts"][key]
        cpu_seconds += shard["cpu_seconds"]
        wall_seconds = max(wall_seconds, shard["wall_seconds"])
        weighted_rate += shard["mean_replicate_seconds"] * shard["replicates_done"]
        complete = complete and bool(shard.get("complete", False))
    payload = {
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "start": 1, "end": 1000, "replicates_done": counts["total"],
        "counts": counts,
        "null_utilities": null_utilities,
        "errors": errors,
        "cpu_seconds": cpu_seconds,
        "wall_seconds": wall_seconds,
        "mean_replicate_seconds": weighted_rate / counts["total"],
        "smoke": False,
        "complete": complete,
        "s0": S0,
    }
    preflight.write_json(payload, os.path.join(out, "analysis",
                                                "null_0001_1000.json"))
    return payload


def combine_final(out):
    """Combine preliminary contrasts with the completed conditional null."""
    with open(os.path.join(out, "analysis", "stats_preliminary.json"),
              encoding="utf-8") as f:
        pre = json.load(f)
    with open(os.path.join(out, "analysis", "null_0001_1000.json"),
              encoding="utf-8") as f:
        null = json.load(f)
    candidate_u = pre["summary"]["CANDIDATE"]["utility_mean"]
    pct = stats.midrank_percentile(null["null_utilities"], candidate_u)
    m = len(null["null_utilities"])
    shuffle_pass = (m >= stats.MIN_VALID_REPLICATES
                    and pct >= stats.MIDRANK_THRESHOLD)
    gates = {
        "BEST-FIXED": pre["contrasts"]["BEST-FIXED"]["pass"],
        "MAJORITY": pre["contrasts"]["MAJORITY"]["pass"],
        "SIMPLE-FEAT": pre["contrasts"]["SIMPLE-FEAT"]["pass"],
        "RANDOM": pre["random"]["pass"],
        "SHUFFLE": bool(shuffle_pass),
    }
    if m < stats.MIN_VALID_REPLICATES:
        final_status = stats.STATUS_INCONCLUSIVE_NULL
    elif not null.get("complete", False):
        final_status = stats.STATUS_INCOMPLETE
    elif all(gates.values()):
        final_status = stats.STATUS_PASS
    else:
        final_status = "NO-GO"
    final = dict(pre)
    final.update({
        "status": final_status,
        "shuffle": {"counts": null["counts"], "midrank_percentile": pct,
                    "pass": bool(shuffle_pass), "cpu_seconds": null["cpu_seconds"],
                    "wall_seconds": null["wall_seconds"],
                    "mean_replicate_seconds": null["mean_replicate_seconds"]},
        "gates": gates,
        "null_errors": null.get("errors", []),
    })
    preflight.write_json(final, os.path.join(out, "analysis", "final_stats.json"))
    return final
