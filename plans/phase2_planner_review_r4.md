# Phase-2 Planner Review R4 — R3 fixes accepted in part; protocol v4 still has decision-level inconsistencies

Date: 2026-10-21
Repository: https://github.com/yujian777555/NeuroEvoScientist
Reviewed substantive Executor commit: `b3ce46bd6129a5b8e9ac5de9b890f2b926cdbf30`
Reviewed status-only commit reported by Executor: `eec1ba2ea4ed3cb50340f66248d6376b6a0c11c5`
Remote branch: `main`

## Decision

**CONDITIONAL HOLD — R3 document repairs are substantial, but G1 is still not ready for CPU preflight.** No data access, CPU preflight, inference, training, or GPU is authorized. The next authorized action is document-only R4 repair, then stop for Planner R5 review.

This is a static review of the actual GitHub protocol/status contents and the substantive commit diff. The Executor reports 111/111 tests passed; those tests were not independently rerun during this review.

## 1. Accepted R3 repairs

- D2 now names five required contrasts and explicit pass criteria for BEST-FIXED, MAJORITY, SIMPLE-FEAT, SHUFFLE, and RANDOM.
- The arithmetic 5,000 × item-config evaluation plan → 45.8 min base → 52.7 min with 15% overhead is internally consistent.
- The 55-minute wall-clock fail-safe is below the 60-minute cap and is explicitly distinguished from measured GPU-active time.
- The partition counts sum to 7,473; pilot subsets are specified as 500/200/300; lock artifacts remain PLANNED and were not created.
- FIT/TUNE/LEVAL roles are more clearly separated, and M1/M2 remain not novelty-cleared.

## 2. Remaining blockers

### R4-A — Predictor classes do not share a defined target/output or selection metric

Protocol §2 proposes:
- ridge regression on Δu;
- logistic regression over a best-config label;
- gradient-boosted trees with max_depth=3 and n_est=100.

Yet FIT cross-validation selects the class using mean held-out **Δu-prediction R²**. Logistic regression over a best-config class label does not predict Δu, and the GBT target/objective is not stated. The regularization parameter α ∈ {0.1, 1, 10} is also not defined for every class (in particular, the listed GBT grid has no corresponding α). The protocol also omits the final refit step after model-class selection and TUNE feature-set selection.

**Required fix:** define a common policy/output contract and a common FIT selection criterion that is meaningful for every candidate class. Either:
1. make all candidate models predict per-action utility differences with class-appropriate, fully defined hyperparameter grids; or
2. let each class produce a config/action policy and select all classes using the same held-out realized utility criterion, with class-specific hyperparameters and deterministic tie-breaks.

Explicitly define the final refit on FIT after the feature set is chosen on TUNE, and before any LEVAL access. Do not report Δu R² for a classifier that does not predict Δu.

### R4-B — SIMPLE-FEAT may be exactly identical to the candidate

The candidate is allowed to choose F0 on TUNE. SIMPLE-FEAT is defined as the “identical pipeline restricted to F0.” If the candidate selects F0, the two policies are identical; the required paired-bootstrap lower bound > 0 is then mathematically impossible. The protocol does not state this consequence.

**Required fix:** choose and freeze one of these paths:
- **Recommended conservative path:** if TUNE selects F0, trigger a pre-specified no-go/early-stop before LEVAL, because the proposed candidate is identical to its required simple-feature comparator and cannot satisfy D2; do not open LEVAL for a doomed test; or
- define a genuinely distinct, fully specified SIMPLE-FEAT baseline and justify why it is a fair simple-feature comparator.

Do not change the baseline after seeing LEVAL results.

### R4-C — SHUFFLE control does not replay the full adaptive selection pipeline

The current SHUFFLE procedure shuffles FIT labels and refits, while the candidate's feature set and thresholds were selected using the original TUNE outcomes. This leaves the null controls with a different selection procedure and can make the comparison invalid.

**Required fix:** specify a permutation control that replays the same adaptive pipeline under each replicate: label/outcome association is broken for both FIT and TUNE in a predeclared, deterministic way; predictor-class/hyperparameter selection, feature-set selection, threshold selection, and final FIT refit are rerun using only the permuted train-side outcomes; then the resulting policy is scored against the same locked LEVAL item outcomes/completions. No new LLM generation is needed for these CPU-side permutations if the per-config outputs are already frozen. If an alternative is chosen, justify exactly what null hypothesis it tests and why it preserves the same selection opportunities as the candidate.

Keep LEVAL outcomes untouched for fitting/tuning and use them only for final scoring. Fix seeds and tie rules before inference.

### R4-D — Primary endpoint hierarchy contradicts itself

Section 3 makes utility at λ=0.1 the primary D2 gate and requires a positive utility-CI lower bound. Section 4 then says raw accuracy, raw token counts, and the Pareto are primary while utility is secondary.

**Required fix:** make the hierarchy consistent. For this learnability pilot, the recommended choice is to explicitly declare **utility at the locked λ=0.1 as the primary D2 pass/fail endpoint**, because D2 is evaluating the utility-driven controller; raw accuracy, prompt/completion tokens, and the accuracy-token Pareto must be separately reported as mandatory secondary outcomes and must not be collapsed into utility. Retain the statement that λ is exploratory-informed and do not claim it is a deployment-optimal price. If the scientific target is instead raw accuracy/Pareto, then the D2 gate must be redesigned before any LEVAL inference.

### R4-E — Missing-value complete-pair deletion can bias the evaluation

The current rule drops an LEVAL item from all contrasts if any configuration is missing for that item. Missingness may correlate with difficult items, so complete-case deletion can bias results and reduce the locked sample without a predeclared validity threshold.

**Required fix:** define a deterministic failure policy. Preferred conservative option: if any required config output is missing or invalid for a LEVAL item, mark the confirmatory run INCOMPLETE/INVALID and do not declare D2 PASS; report the failure count and do not rerun selectively. If instead failures are scored, predefine incorrectness and token-cost accounting in detail. Do not silently drop items.

### R4-F — ID normalization is incomplete for source-provided IDs

Section 1 specifies NFC/whitespace normalization for fallback question text, but when a stable source ID field exists it says to use that field without applying the same normalization/canonicalization rules. Hash input encoding and deterministic tie-breaks for equal sort keys are also not explicit.

**Required fix:** specify canonical string conversion for source IDs; apply Unicode NFC, leading/trailing trim and internal-whitespace collapse consistently; fail on empty or duplicate normalized IDs; specify UTF-8 encoding and exact hash bytes; sort by (digest, normalized ID) to make tie-breaking deterministic. Keep all actual lock files PLANNED and uncreated.

### R4-G — Bootstrap interval construction is not fully specified

The protocol says “95% paired-bootstrap CI” but does not state percentile vs BCa/basic, quantile interpolation convention, or whether the lower-bound test uses a two-sided 95% interval.

**Required fix:** choose and document one deterministic interval construction (e.g., percentile bootstrap with the 2.5th/97.5th percentiles, explicit quantile convention, 10,000 paired item-level resamples, seed S0), and consistently apply it to all bootstrap contrasts.

### R4-H — status.json still contains stale R2 pointers

The latest `status.json.phase2_planning` has `next_gate` updated to R4, but `planner_review` and `executor_prompt` still point to R2 files, and `open_items` / `authorized_now` retain R3-era instructions. The `documents` list also does not clearly list the R3 review and prompt.

**Required fix:** in the next status update, modify only `phase2_planning`; update the current review/prompt pointers and document list; distinguish the reviewed R3 deliverable, R4 repair deliverable, status-only commits, and observed remote HEAD. Do not self-reference the commit that contains the final status value.

## 3. R5 and novelty verdict unchanged

- Plain embedding+MLP TACC: **PIVOT**.
- DEFLECT and MEMROUTE: **NOT CLEARED**.
- No “first” or “no prior work” claim is allowed.
- The conformal scan is a targeted scan, not a claim that all adjacent literature has been exhausted.

## 4. Authorization boundary

- GPU authorization: **0**.
- Controller implementation/training/inference: **not authorized**.
- Dataset loading, partition-lock generation, MATH-500 access: **not authorized**.
- CPU preflight: **not authorized yet**.
- Frozen V1/V2 papers, PDFs, supplements, and historical F1/F2 results must remain untouched.

Only document-only R4 repairs are authorized. After pushing them, stop for Planner R5 review. CPU preflight and GPU Pilot each require separate explicit approval.

## 5. Final R4 verdict

**R3 fixes accepted in part. Protocol v4 still requires a final consistency repair before CPU preflight; no experiment is authorized.**
