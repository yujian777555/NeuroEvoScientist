# Phase-2 Planner Review R2 — R1 repairs substantially accepted; Pilot remains on HOLD

Date: 2026-10-21
Repository: https://github.com/yujian777555/NeuroEvoScientist
Reviewed executor deliverable commit: `7f46cf2fd10b0021e8935d80303ca4a224a292b8`
Status-update commit reported on main: `9ca92a30b42b84c10dbe7f905048b4567fe322ac`
Observed GitHub `main` HEAD at review time: `9ca92a30b42b84c10dbe7f905048b4567fe322ac`

## Decision

**CONDITIONAL HOLD — no GPU Pilot authorization.** The Executor made real substantive changes, and most explicit R1 requests are addressed. However, the revised G1 protocol still omits a required baseline condition, makes an unsupported precision claim, and leaves the pilot sample/selection protocol insufficiently operational. These are fixable document-level issues; they do not require new experiments.

The remote commit history confirms the two new commits. The Executor reports a clean local working tree; GitHub's remote API does not independently expose that local working-tree state.

## 1. R1 items accepted

- R5 matrix expanded from 10 to 16 paper rows, with row-level evidence-depth and code-availability labels.
- BudgetMem, Gated-Memory Routing, and PILOT are added and compared by mechanism rather than treated as identical systems.
- The broad embedding+MLP TACC novelty claim is correctly marked PIVOT.
- DEFLECT and MEMROUTE remain hypotheses, not cleared novelty claims.
- The utility is now defined per item, with prompt and completion tokens counted separately in the numerator and dataset utility defined as a mean.
- The original 12,000-generation estimate is correctly corrected: at 55 seconds per 100 item-config evaluations, it is 6,600 seconds, about 110 minutes or 1.83 GPU-hours.
- The new 5,500-generation arithmetic is internally correct: 3,025 seconds = 50.4 minutes = 0.84 hours; a 15% overhead gives about 0.97 hours.
- The report explicitly says the pilot was not run, no GPU was used, MATH-500 was untouched, and novelty is not cleared.

## 2. Blocking corrections before any Pilot decision

### R2-A. D2 pass conditions are incomplete

R1's repair instruction required the feature-driven policy to demonstrate out-of-sample gain over the best fixed policy and to outperform shuffled-label, reasonable random, and simple feature baselines. The current protocol makes only these two conditions explicit as D2 pass criteria:
1. feature-policy utility exceeds best-fixed utility with a paired CI excluding zero;
2. it beats a shuffled-label control.

The protocol says majority-action and random-policy results are merely “reported”; length/number-only and feature-only models are listed as ablations but are not required for a pass. This does not fully implement R1.

**Required fix:** pre-specify the D2 gate so the candidate must beat:
- the train-side-selected best fixed configuration;
- shuffled-label control(s), with the shuffle seed/count locked before LEVAL;
- a reasonable random policy;
- a majority/action-frequency policy, if applicable to the action space;
- a simple feature baseline (at minimum length/numeric-density-only).

Define each paired contrast and its uncertainty calculation. Freeze one candidate model and all thresholds before LEVAL. Do not choose the best candidate, baseline, seed, or threshold after inspecting LEVAL. State how the multiple comparisons are handled; a hierarchical/intersection-union gate is acceptable if fully specified.

### R2-B. The 800-item train-side sample and 300-item LEVAL subset are underspecified

The partition table allocates the 7,473 GSM8K train examples approximately as BANK=2,989, FIT=1,868, TUNE=1,121, and LEVAL=1,495. The budget section then says “800 FIT+TUNE items” plus “300 LEVAL items,” without specifying the exact FIT/TUNE counts or the deterministic procedure for selecting the 300-item LEVAL subset.

The text also says predictor fitting happens on FIT while “cross-fitting inside FIT∪TUNE” is used for model/feature choices. That wording leaves the actual fit/tune boundary ambiguous.

**Required fix:** state exact counts and a deterministic selection rule. A proportional 800-item allocation would be 500 FIT + 300 TUNE; another allocation is acceptable only if justified. Specify:
- fixed random seed and stable ID normalization;
- exact ID list and SHA-256 for each pilot subset;
- whether the 300 LEVAL items are a subset of the 1,495-item LEVAL partition;
- that the LEVAL subset is selected before any candidate outputs are generated;
- which operations use FIT, which use TUNE, and the exact role of cross-fitting;
- how the best-fixed configuration is selected without LEVAL access.

The current document-only deliverable does not itself provide a lock artifact or the exact hash of the proposed 300-item LEVAL subset. Until a later explicitly authorized CPU preflight produces/verifies those artifacts, describe the split as **planned**, not already locked in practice.

### R2-C. The claimed ±2–3 percentage-point precision is not established

The protocol says n=300 “gives” a paired bootstrap CI half-width of about ±2–3pp. That is not guaranteed by sample size alone, especially because the endpoint includes token-cost utility as well as binary correctness.

For orientation only, for a near-zero paired binary accuracy difference with n=300, the approximate 95% half-width is (1.96\sqrt{q/300}), where (q) is the paired discordance rate:
- q=5%: about ±2.5pp;
- q=10%: about ±3.6pp;
- q=20%: about ±5.1pp;
- q=40%: about ±7.2pp.

These are analytic planning scenarios, not observed results; utility differences may have wider intervals because token counts vary.

**Required fix:** remove the unconditional precision claim. Use available historical paired logs, if appropriate and clearly labeled as planning-only, to give a range of discordance and token-variance scenarios. State the minimum detectable effect under explicit assumptions, or say the pilot is a learnability screen with uncertain power. Do not promise that n=300 can resolve ±2–3pp without evidence.

### R2-D. Reconcile the throughput basis and 1.0 GPU-hour cap

The arithmetic is correct, but the 0.97-hour estimate leaves only about 1.8 minutes below a 1.0-hour hard cap. Clarify whether the reported 55 seconds per 100 item-config evaluations includes memory-bank construction, cache misses, and all five configurations. The current protocol adds 15% for bank build/cache misses, so the timing basis must say whether that is incremental or potentially double-counted.

**Required fix:** no new benchmark. Reconcile existing logs and define GPU-hour accounting. Either justify the estimate as a conservative upper bound with adequate margin or revise the sample/budget proposal. Do not treat the requested 1.0 GPU-hour as authorized.

### R2-E. Correct formula and protocol terminology

The displayed algebra currently contains an incorrect intermediate expression: `0.1·λ·1,000/1,000`. The correct calculation for the stated utility is:

`λ × 1,000 / 10,000 = 0.1 × 0.1 = 0.01`.

Also replace “pre-registered” / “Pre-registered D2 pass” with **“pre-specified and commit-locked before LEVAL inference”** unless a formal external preregistration actually exists. Remove stale references to the former `VAL` partition where they are not intentional.

### R2-F. Extend the conformal/decision-aware routing scan

The current R5 audit is materially better but explicitly leaves the conformal-deferral scan unresolved. Add and scope-distinguish at least:

- **Fang & Nalisnick, “Learning to Defer with an Uncertain Rejector via Conformal Prediction,” TMLR 2026** — uncertainty-aware deferral with conformal sets for model-versus-expert routing under shift. This is adjacent prior art for uncertain rejectors, not a direct match to single-frozen-LLM scaffold routing with a token-cost floor. Paper/project: https://yiziruifang.com/project/uncertain-defer/ ; OpenReview: https://openreview.net/forum?id=wrLiUpfk4s
- **Tan, Rangwala & Maddix, “Threshold-Aware Conformal Routing” (arXiv:2610.02487, 2026)** — decision-aware conformal routing between a surrogate and an expensive simulator around a fixed decision threshold. It is not an LLM scaffold router, but it is relevant to the broad claim of uncertainty/threshold-aware deferral. https://arxiv.org/abs/2610.02487

Do not label either as a direct collision without a mechanism comparison. Record actual verification depth and code status. If the paper is only read from an abstract or project page, label that honestly. After this pass, retain the R5 verdict as **PIVOT / novelty not cleared** unless evidence supports a stronger conclusion.

## 3. Status consistency correction

The current `status.json` still has stale state:
- `next_gate` says Kimi should perform the R1 repair that is now reported complete;
- `blockers` still list R1's resolved omissions without distinguishing them from remaining blockers;
- `g1_protocol` still describes BANK/LABEL/VAL rather than BANK/FIT/TUNE/LEVAL;
- `reviewed_executor_deliverable_commit` still points to the earlier `8af0a58`;
- the report says `last_commit` is the current HEAD, but the JSON's `last_commit` is `7f46cf2` while current remote HEAD is `9ca92a3`.

Update `phase2_planning` so its semantics are explicit: distinguish the latest substantive Executor deliverable commit from the latest observed remote HEAD/status update. Do not claim the status file can self-reference the hash of the commit that contains its own final value. Update `next_gate`, blockers, protocol path/summary, current HEAD, and remaining open items consistently.

## 4. Authorization and next gate

- **GPU authorized: 0.**
- **Pilot status: NOT AUTHORIZED, NOT EXECUTED.**
- No controller implementation, training, inference, or MATH-500 access.
- No changes to frozen V1/V2 paper artifacts or historical F1/F2 results.

After the document-only corrections, stop for Planner R3 review. If that review passes, a separate CPU-only preflight may be authorized to create and verify immutable partition/subset locks and run overlap/contract tests. GPU Pilot authorization, if any, will be a separate explicit decision.

## 5. Verification references

- Executor deliverable: https://github.com/yujian777555/NeuroEvoScientist/commit/7f46cf2fd10b0021e8935d80303ca4a224a292b8
- Status update: https://github.com/yujian777555/NeuroEvoScientist/commit/9ca92a30b42b84c10dbe7f905048b4567fe322ac
- Current remote HEAD at review time: `9ca92a30b42b84c10dbe7f905048b4567fe322ac`

**Final R2 verdict: R1 repair substantially accepted; G1 NOT PILOT-READY; no GPU authorization.**
