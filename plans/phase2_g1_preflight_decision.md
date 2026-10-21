# Phase-2 G1 Preflight Decision v4 — Executor Report (2026-10-21)

Authority: `plans/phase2_planner_review_r3.md`,
`plans/phase2_g1_pilot_repair_prompt_r3.md`.
Scope executed: document-only edits to
`plans/phase2_g1_revised_protocol.md` (v4), this file, and
`status.json.phase2_planning`. **0 GPU, 0 inference, 0 training, no
controller code, no dataset access, no partition locks created, no CPU
preflight, MATH-500 untouched, V1/V2 frozen artifacts untouched.**

## R3 issue-by-issue resolution

| R3 item | Status | Resolution (protocol v4) |
|---|---|---|
| R3-A — MAJORITY/SIMPLE-FEAT pass rules undefined | DONE | §3: all five contrasts have explicit numeric rules. MAJORITY and SIMPLE-FEAT: paired per-item utility difference on LEVAL_pilot, 95% paired-bootstrap CI lower bound > 0 (item-level resampling, n=300, 10,000 resamples, seed S0=20261021). SHUFFLE/RANDOM: 1,000 shuffles/draws with locked seed streams and a mid-rank 95th-percentile rule (ties specified). Missing-value complete-pair rule predeclared; McNemar secondary; intersection–union gate: D2 PASS ⟺ all five pass |
| R3-B — 45-min abort contradicted worst case | DONE | v3's 45-min abort withdrawn. Coherent set: worst case 45.8 min, +15% = 52.7 min; **wall-clock fail-safe abort at 55 min** (margins: 2.3 min over worst-case-plus-overhead, 5 min under the 60-min cap); single-GPU ⇒ GPU-active ≤ wall-clock, so the fail-safe bounds GPU-active ≤ 0.92 GPU·h; planned (not yet run) pynvml GPU-second metering in the manifest; wall-clock never reported as GPU-active; abort ⇒ INCOMPLETE, no partial averages |
| R3-C — FIT/TUNE selection overlap | DONE | §2: one ordered procedure with predeclared grids. FIT_pilot 5-fold cross-fitting selects ONLY (predictor class, α) by Δu-R²; TUNE_pilot selects feature set {F0, F1} and (δ, τ) with class/α frozen; BEST-FIXED selected by FIT cross-fitted utility alone, TUNE confirmation cannot change it; deterministic complexity-first tie-breaks; all frozen before LEVAL |
| R3-D — partition algorithm + provenance | DONE | §1.1 fully defines the future lock generation: ID normalization (NFC, whitespace collapse, empty→FAIL), namespace-separated hash ordering (`phase2-partition-v1` / `phase2-subset-v1`), exact counts 2,989/1,868/1,121/1,495 = 7,473, subset counts 500/200/300, and the complete artifact list (source revision+SHA, per-partition and per-subset ordered ID lists + SHA-256, disjointness proofs, historical-split overlap checks). Locks remain PLANNED — none created this round |

## status.json provenance semantics (R3-D second half)

`phase2_planning` now distinguishes explicitly:
- `remote_head_at_r3_start`: `99a621738156b6626e1960d00652967e549fbc23`
- `r3_deliverable_commit`: set to this round's substantive commit
  (recorded after commit; see field);
- status-only commits are never claimed to be deliverable commits;
- no field claims to name the hash of the commit that contains itself.

## Consistency checks actually run (this round)

- `status.json` parses as valid JSON (python json.load).
- `phase2_r5_overlap_matrix.csv` parses; 18 rows (unchanged this round).
- Arithmetic recheck: 2,989+1,868+1,121+1,495 = 7,473 ✓; 5×(500+200+300)
  = 5,000 ✓; 5,000/100×55 = 2,750 s = 45.8 min ✓; ×1.15 = 52.7 min ✓;
  52.7 < 55 (abort) < 60 (cap) ✓; λ×1000/10000 = 0.01 ✓.
- Full test suite re-run: 111/111 PASS (no code changed; confirms no
  collateral damage).
- Forbidden-scope diff check: only the two plan documents + status.json
  modified; no V1/V2/R5-result files touched.
- Terminology grep: no "pre-registered" outside change-log quotes.

## Explicitly NOT done

- No partition locks, no CPU preflight, no GPU, no inference/training, no
  dataset access, no MATH-500 access.
- M1/M2 novelty remains NOT CLEARED; plain TACC remains PIVOT.
- Budget request ≤ 1.0 GPU·h is a proposal, NOT an authorization.

**R3 DOCUMENT REPAIRS COMPLETE — STOP AND WAIT FOR PLANNER R4 REVIEW**
