# Phase-2 Planner Review R3 — R2.1 substantially accepted; final protocol clarification required

Date: 2026-10-21
Repository: https://github.com/yujian777555/NeuroEvoScientist
Reviewed substantive Executor commit: `bd21c3363b603606cfefa1ee95ade59f9ae0681d`
Latest remote `main` HEAD observed before this review: `99a621738156b6626e1960d00652967e549fbc23`

## Decision

**CONDITIONAL HOLD. R2.1 is a real and substantial document revision, but the protocol is not yet ready for CPU preflight. GPU authorization remains 0.** The literature expansion and most R2 corrections are accepted. Only a narrow document/status repair is authorized next; no data access, CPU preflight, inference, or GPU.

## 1. Accepted R2.1 work

- The D2 battery now names best-fixed, shuffled-label, random, majority-action, and simple-feature baselines.
- The unsupported unconditional ±2–3pp precision claim has been withdrawn; discordance scenarios and token-variance caveat are provided.
- Utility algebra and pre-specified/commit-locked terminology are corrected.
- R5 adds two conformal/decision-aware routing works with honest verification-depth labels; M1/M2 remain NOT CLEARED.
- Budget arithmetic for 5,000 generations is internally consistent at the stated assumptions: 5,000/100 × 55 s = 2,750 s = 45.8 minutes; +15% = about 52.7 minutes = 0.88 hours.
- The report explicitly states that partition locks were not created, no data was loaded, and no GPU/inference/training occurred.

## 2. Remaining blockers

### R3-A — D2 control-pass rules are incomplete

Protocol §5 says the candidate must beat MAJORITY and SIMPLE-FEAT, and says controls 2–5 must pass their pre-specified rule. However, it only gives explicit numeric pass rules for SHUFFLE and RANDOM (candidate exceeds the 95th percentile of their utility distributions). It does not specify a statistical pass rule for MAJORITY and SIMPLE-FEAT.

**Required fix:** for each of MAJORITY and SIMPLE-FEAT, define a paired per-item utility contrast against the frozen candidate and require its pre-specified 95% paired-bootstrap CI lower bound to be greater than zero (or justify a different explicit rule). State the bootstrap resample unit and seed. If exact McNemar is reported for accuracy, keep it secondary to the primary utility gate. State how all control rules fit the intersection–union gate; do not leave “must beat” operationally undefined.

### R3-B — 45-minute abort conflicts with the documented worst-case estimate

The protocol calculates 5,000 evaluations at 55 seconds/100 = 2,750 seconds = **45.8 minutes before overhead**. It then adds 15%, giving about **52.7 minutes**, yet says to abort at **45 minutes**. Under the protocol's own worst-case assumptions, the run would hit the wall-clock abort before finishing even before overhead.

**Required fix:** without running a benchmark, choose and justify a coherent plan:
- reduce the number of evaluations enough that the stated worst-case plus overhead fits within the abort window with explicit margin; or
- revise the wall-clock abort threshold and demonstrate that it still leaves a defensible margin to the requested one-hour cap.

Do not call wall-clock hours “aggregate GPU-hours” unless the hardware/concurrency assumption and metering relationship are explicit. The previous logs did not separately meter GPU-active time. If the future run's GPU-hour cap cannot be enforced from reliable telemetry, say so and define the guard instrumentation and a separate wall-clock fail-safe. This is still a budget proposal, not authorization.

### R3-C — feature-selection responsibilities overlap

Protocol §1 currently says:
- FIT-only cross-fitting chooses “model-class/feature choices”;
- TUNE chooses thresholds, lambda sensitivity, and “feature set.”

These are overlapping feature-selection decisions and leave it unclear which features are actually frozen before LEVAL.

**Required fix:** define a single ordered selection procedure. For example, FIT-only cross-validation may choose the predictor class/regularization from a predeclared candidate set; TUNE may choose among a separately predeclared feature-set/threshold grid, but then FIT cross-validation must not also choose that feature set. Alternatively use another clear nested scheme. Specify the exact candidate grid and a deterministic tie-break rule. Freeze all choices before LEVAL.

Also define the best-fixed selection rule precisely: whether FIT cross-fitted utility alone selects it and TUNE only reports a confirmation, or a predeclared FIT+TUNE rule selects it. No LEVAL data may enter this choice.

### R3-D — partition-generation and status provenance are still incomplete

The v3 protocol gives a deterministic hash-order algorithm for selecting pilot subsets *within partitions*, but does not state the exact deterministic algorithm for assigning all 7,473 source items to BANK/FIT/TUNE/LEVAL. The actual partition and subset locks are correctly marked PLANNED and must remain uncreated this round; the protocol should nevertheless define the future lock-generation algorithm fully (stable ID normalization, namespaced seed/hash ordering, exact partition counts, exact subset counts, and lock artifacts).

The current `status.json` still has stale provenance fields, including `reviewed_commit` / `reviewed_executor_deliverable_commit` pointing at the R1 deliverable, and `status_update_base_head` pointing at an older Planner commit. Update only `phase2_planning` to distinguish:
- latest substantive Executor deliverable commit (`bd21c33...`);
- latest observed remote HEAD at the start of this R3 repair (`99a6217...`);
- subsequent status-only commits.

Do not claim the status file can self-reference the commit that contains its final value.

## 3. R5 verdict

R5 work is accepted as an audit expansion, not as a novelty clearance:
- plain embedding+MLP TACC: **PIVOT**;
- DEFLECT and MEMROUTE: **NOT CLEARED**;
- the conformal scan is acceptable as a targeted scan with Fang & Nalisnick explicitly PARTIAL, not as a claim that all related work was read in full;
- final submission-time re-audit, especially exemplar-selection work and any new Forge/ARC/BudgetMem versions, remains mandatory.

Do not make a “first” or “no prior work” claim.

## 4. Authorization boundary

Current authorization:
- GPU: **0**;
- controller implementation/training/inference: **not authorized**;
- dataset loading, partition-lock generation, MATH-500 access: **not authorized**;
- CPU preflight: **not authorized yet**;
- frozen V1/V2 artifacts and historical F1/F2 results must remain untouched.

Next action: document-only R3 repairs, push and stop for Planner R4 review. If R4 passes, a separate explicit decision may authorize CPU-only lock generation and overlap checks. GPU Pilot approval, if any, is a later independent gate.

## 5. Final R3 verdict

**R2.1 substantially accepted; protocol requires a final document-only clarification before CPU preflight. No experiment is authorized.**
