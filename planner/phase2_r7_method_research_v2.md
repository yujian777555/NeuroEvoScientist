# Phase-2 R8 Method Research v2 — Full-Information Policy Learning and Statistical Repair

Date: 2026-10-28
Status: **R8_DOCUMENT_REPAIR_COMPLETE — WAITING FOR PLANNER R9 REVIEW**. This is a document-only correction, not an implementation or an experiment authorization. The original R7 document is retained as history.

## 1. What R7 got right, and what had to change

R7 correctly preserved the frozen R1 failure: CANDIDATE utility 0.6279553, B2 0.6410255, B1/MAJORITY 0.6371011, SIMPLE-FEAT 0.6345941; all three paired fixed/simple contrasts span zero; SHUFFLE has 749 F0-NO-GO and only 251 valid F1-scored replicates (<950), so it remains `INCONCLUSIVE_NULL`. R6's stop decision remains authoritative.

The statistical repair is fundamental: R1 evaluates **all five configurations on every evaluated item** (3,500 Stage-1 generations and 1,500 LEVAL generations). These are full-information per-item action outcomes, not a logged action and its reward. An inverse-propensity residual built for partial-feedback/off-policy data is therefore unnecessary and would answer the wrong question. No candidate in this v2 is called doubly robust, and no inverse-propensity weight is used.

R8 also corrects three separate hypotheses that R1 cannot by itself settle:

- **H1 — heterogeneity exists.** Supported: the best action varies by item, and an optimistic in-sample upper bound is numerically much higher than the fixed baselines (0.8207188 on LEVAL).
- **H2 — action differences are predictable from pre-action features.** Not established: that upper bound uses each item's actual outcomes and does not demonstrate that features can predict them.
- **H3 — a learned policy beats the strongest fixed baseline on fresh data.** Not established: CANDIDATE is below B2, B1/MAJORITY, and SIMPLE-FEAT on observed utility, and the fixed/simple CIs span zero.

The 0.8207188 figure is not statistical significance, not a deployable policy result, and not evidence of feature-predictable gains. It is only an optimistic upper bound computed with hindsight. Likewise, the action-allocation confusion (CANDIDATE selects B0 in only 2 of 96 B0-best items and B2 in only 3 of 9 B2-best items) is evidence of misallocation, not proof that a different estimator will work.

## 2. Full-information versus partial-feedback statistical settings

### 2.1 Current setting: full-information contextual policy learning

For each item \(i\), the frozen record contains correctness, prompt tokens, completion tokens, and raw completion for every action \(c\). Utility remains

\[
U_i(c)=\mathrm{correct}_i(c)-0.1\,
\frac{\mathrm{prompt}_i(c)+\mathrm{completion}_i(c)}{10000}.
\]

For deterministic policies \(\pi\) and a fixed baseline \(\pi_0\), direct paired policy-difference evaluation is

\[
\widehat\Delta(\pi,\pi_0)=\frac1n\sum_{i=1}^n
\left[U_i(\pi(x_i))-U_i(\pi_0(x_i))\right].
\]

For a stochastic policy, replace \(U_i(\pi(x_i))\) by \(\sum_c\pi(c\mid x_i)U_i(c)\). This is direct full-information evaluation, not DR. It requires train/tune/confirmation separation or cross-fitting to avoid in-sample policy selection, but it does not require propensities.

### 2.2 Distinct alternative: partial-feedback/off-policy learning

A genuine partial-feedback study would require a randomized logging policy \(h(a\mid x)\), known positive action probabilities, the observed-feedback protocol, and added data/compute cost. Only then could residual weighting be meaningful:

\[
z_i(\pi)=\sum_a\pi(a\mid x_i)\hat m_a(x_i)
+\frac{\pi(A_i\mid x_i)}{h(A_i\mid x_i)}\{U_i-\hat m_{A_i}(x_i)\}.
\]

That would be a different, more expensive study requiring separate approval. It is not authorized and is not the current design. Positivity/support conditions \(\pi(a\mid x)>0\Rightarrow h(a\mid x)>0\) would be mandatory. This alternative is included only to prevent future estimator mismatch.

## 3. Failure diagnosis and evidence strength

### 3.1 Heterogeneity is real but not necessarily learnable

The best action varies: B1=160, B0=96, B3=17, REF=18, B2=9 on LEVAL. There is an optimistic upper bound of 0.8207188. This supports H1 and shows action-space headroom, but does not establish H2 or H3.

### 3.2 Action-value estimation is the most concrete defect

Median best-vs-second utility gap is 0.002135; 89% are below 0.05 and 85% below 0.005. A hard argmax can turn estimation errors into systematic wrong configurations. The candidate's actual choices confirm misallocation. This supports studying baseline-relative utility-difference prediction and conservative abstention, not simply adding a more complex classifier.

### 3.3 Representation and shift evidence is weaker

F1 does not outperform SIMPLE-FEAT on utility, but there is no proof that a particular missing feature would help. `ShiftDetector` is only a kNN distance in feature space, not a validated OOD detector or a guarantee of safer behavior. Any new shift mechanism needs independent shift evaluation rather than distance-threshold folklore.

### 3.4 Utility and evaluation costs

The utility formula is valid for generation-token trade-offs, but it omits controller training, embedding, and offline analysis costs. The permutation phase consumed 523,065 CPU-seconds. Therefore total deployment cost must be reported separately; the primary endpoint cannot be silently redefined to make the controller look cheaper.

### 3.5 SHUFFLE is a conditional, underpowered diagnostic, not a clean null

The 749 F0-NO-GO replicates are not silent deletions: they are counted and reported. The 251 valid F1 scores are conditional on selecting F1 and cannot be interpreted as an unrestricted null distribution. With <950 valid scores, the correct outcome is `INCONCLUSIVE_NULL`, not proof of either superiority or universal futility. RANDOM passing does not change the fixed-baseline failures.

## 4. Candidates after statistical repair

**Ranking.** FIDL ranks first because it directly matches the observed action-value misallocation, uses the existing full-information outcomes without new logging assumptions, and has the lowest proposed implementation and evaluation cost. FCC ranks second because marginal conformal calibration is a distinct uncertainty mechanism, but its exchangeability requirement and lack of a shift guarantee may reproduce the current generalization failure. RRC ranks third because residual escalation adds cumulative inference cost and its closest prior work leaves the least clear independent contribution. This ordering is a research-priority judgment, not evidence that any candidate works or is novel.

### Candidate 1 — **FIDL: Full-Information Difference Learner with LCB abstention**

**Question.** Can baseline-relative utility-difference prediction, with a conservative confidence-gated fallback, reduce harmful switches enough to beat the strongest fixed configuration on untouched data?

**Target.** For each action \(a\), learn \(\Delta_i(a)=U_i(a)-U_i(B1)\). Also evaluate against B2 as the strongest fixed comparator. This is preferable to predicting only the best-action label because it preserves the magnitude and sign of utility gain, including the near-tie regime where classification labels are unstable.

**Training.**

- Predictor: an L2-regularized linear model or shallow GBT, using only pre-action features. Start with the linear model for interpretability; GBT remains an ablation, not a presumed improvement.
- Loss: per-action Huber loss on \(\Delta_i(a)\) to reduce outlier sensitivity, with an L2 complexity penalty for the linear model and predeclared depth/leaf regularization for GBT. Thus the linear candidate is Huber regression, not squared-error ridge. No inverse propensities and no DR label.
- Nested design: inner FIT folds select predictor class/hyperparameters by realized held-out utility. TUNE then selects only the predeclared feature set and decision thresholds. The selected model is refit on FIT only with the chosen features; TUNE never supplies model-fitting examples, and LEVAL is never touched for selection.

**Decision.** On TUNE only, compute the mean paired utility difference of the FIT-refit candidate against B1 and the FIT-selected BEST-FIXED comparator with a paired percentile bootstrap (10,000 resamples, type-7, fixed seed). Deploy the candidate's predicted-utility argmax policy only when both one-sided lower confidence bounds exceed the predeclared margin δ=0.01; otherwise return B1. Requiring both bounds is an intersection–union selection rule, not two optional cherry-picked tests. If either interval is too wide, treat the result as NO-GO rather than forcing deployment. The chosen policy and all thresholds are then frozen before the new confirmation set is accessed.

**Existing pieces vs possible contribution.** Direct-method contextual policy learning, safe policy improvement with LCB, and pairwise ranking already exist. The only possible new combination is *full-information, baseline-relative token-utility difference learning with an explicit B1 cost floor and LCB abstention for frozen-LLM scaffolds*. Novelty remains **NOVELTY_UNRESOLVED**: the combination may be an application of known safe-selection ideas rather than a new algorithm.

**Falsification.** FIDL must beat BEST-FIXED with CI lower bound >0 and must outperform direct GBT and no-LCB controls. Wide intervals, support failure, no advantage over B2, or no advantage over direct GBT are all stop conditions.

**EC necessity.** None. This is a small supervised estimation problem, not a combinatorial search.

### Candidate 2 — **FCC: Full-information conformal abstention**

**Question.** Can a one-sided conformal lower bound for utility gain produce a distribution-free abstain-to-B1 rule without pretending that it also solves distribution shift?

**Mechanism.** On FIT, compute \(G_i(a)=U_i(a)-U_i(B1)\). On a separate calibration split, define nonconformity \(s_i(a)=-G_i(a)\) and let \(q_a\) be the conformal quantile at level \(1-\alpha\) using the standard split-conformal order statistic. The lower-bound rule is \(-q_a>\delta=0.01\); otherwise B1. For multiple actions, use a predeclared intersection–union gate rather than selecting the best-looking interval after inspection. Any empty/ambiguous set triggers abstention.

**Evidence and limits.** Split-conformal coverage is marginal under exchangeability, not a remedy for distribution shift. If shift diagnostics fail, status is INCONCLUSIVE rather than a claimed valid gate. TACR-style threshold-local width shaping can be compared only as an ablation.

**Existing pieces vs possible contribution.** Conformal deferral and threshold-aware conformal routing already exist. The only possible new combination is *one-sided continuous utility-gain calibration with an explicit B1 cost floor and multi-action IUT for frozen-LLM configurations*. Novelty remains **NOVELTY_UNRESOLVED**.

**Falsification.** FCC must satisfy the declared coverage target on held-out calibration and improve utility over direct GBT. Invalid coverage, excessive abstention, or no advantage over B2 stops the method.

**EC necessity.** None. Calibration is deterministic and cheap.

### Candidate 3 — **RRC: Residual-Recovery Cascade with full-information gating**

**Question.** Can starting with a cheap valid configuration and adding more expensive configurations only for predicted recoverable failures beat both hard argmax and fixed baselines after all cumulative tokens are charged?

**Mechanism.** Start with B0 or B1. On a residual validation set, identify items where the current configuration fails. For each more expensive action \(a\), estimate \(U_i(a)-U_i(\text{current})\) after all cumulative prompt and completion tokens. Add \(a\) only if the lower confidence bound of incremental utility is positive. Otherwise stop with the current cheap configuration. If no residual recoverability is demonstrated, stop with B1.

**Existing pieces vs possible contribution.** Adaptive-Solver already uses residual wrong-sets and consistency-triggered escalation. The only possible difference is *full-information incremental-utility gating with exact cumulative token accounting and no consistency requirement*. Novelty remains **NOVELTY_UNRESOLVED** and may be too close to Adaptive-Solver to justify a separate algorithm.

**Falsification.** RRC must beat B1 and B2 after all cumulative tokens. If escalation costs exceed recovered utility, or no residual failures are recoverable, stop. If it cannot outperform a simple B1 fallback, reject it.

**EC necessity.** None. A residual cascade is a deterministic finite sequence, not a search problem requiring EC.

## 5. Closest-work and novelty audit

This targeted comparison narrows the mechanism audit and retains the full bibliographic records and links in `planner/phase2_r7_method_research.md` §5. It is not an exhaustive novelty clearance.

| Prior mechanism | What is already established | What remains unproven for these candidates |
|---|---|---|
| Direct-method contextual policy learning and pairwise ranking | Utility/difference prediction and direct action-value models are established. | Whether full-information baseline-relative token utility with LCB abstention adds anything beyond a new dataset/configuration. |
| Safe policy improvement with LCB | Selecting by lower confidence bound and otherwise retaining behavior policy is established (Jiang–Li and later direct policy-difference CSs). | FIDL cannot be called novel merely for using LCB on an LLM scaffold. A distinct support/full-information and cost-floor formulation is required but unproven. |
| Selective prediction / learning-to-defer | Confidence-triggered abstention and cost-sensitive deferral to a human/expert are established. | B1 as an explicit cheap generation-config fallback is different in target but not automatically novel. |
| Conformal routing and selective classification under shift | Conformal correctness/uncertainty and threshold-aware scalar routing are established. | FCC's multi-action utility-gain calibration with IUT and shift failure reporting is only a possible new combination, not a validated algorithm. |
| LLM strategy/scaffold routing | Query routing among models, prompting strategies, retrieval depths, and agent workflows is established (RouteLLM, RTR, Chen, Adaptive-RAG, MaAS). | The remaining distinction must be full-information utility estimation with rigorous fixed/simple contrasts, not a renamed router. |
| Agent/workflow evolution (ADAS, AlphaEvolve, AgentSquare, MaAS) | Code/workflow/supernet evolution and archives already exist. | No candidate should add EC by analogy. A combinatorial bottleneck and equal-budget heredity benefit are unproven. |

**Novelty conclusion:** all three candidates remain **NOVELTY_UNRESOLVED**. If no evidence emerges that their exact combination exceeds these mechanisms, the appropriate decision is to stop rather than package an algorithmic contribution.

## 6. Negative controls and revised statistical plan

### 6.1 Primary evaluation

Use direct full-information paired utility differences on a new untouched confirmation set. The primary contrast is candidate − BEST-FIXED with a paired percentile 95% CI (10,000 resamples, type-7, fixed seed). Secondary outcomes are raw accuracy, prompt tokens, completion tokens, accuracy–token Pareto, controller inference/training cost, and offline analysis cost.

### 6.2 SHUFFLE and RANDOM as secondary diagnostics

If permutation controls are retained:

- The full replicate count is 1,000. The unconditional report must include total replicates, F0-NO-GO, invalid/errors, and valid F1-scored replicates.
- F0-NO-GO is not silently removed: it remains in the accounting, but no utility is fabricated for it. Valid F1 replicates are the only ones used for the conditional mid-rank.
- Conditional mid-rank is explicitly conditional on selecting F1. It is not an unconditional permutation p-value and cannot by itself validate learnability. If valid replicates are <950, the result is INCONCLUSIVE_NULL, not a pass.
- Every valid replicate replays the complete model/feature/threshold selection pipeline on permuted full outcome vectors, not just a refit on FIT labels. Fitting/tuning on LEVAL remains forbidden.
- Invalid/error replicates are reported separately and never silently discarded. Do not increase replicates after seeing the outcome or change the denominator.

### 6.3 Why not blindly inherit the old gate

The old SHUFFLE gate is an association diagnostic, not a substitute for the full-information policy-superiority question. The 25.1% valid rate makes it underpowered as a main proof. The primary gate should be the direct paired full-information contrast, with SHUFFLE/RANDOM used only as secondary negative controls and with the conditional limitation stated explicitly.

## 7. Pre-registration draft for FIDL (not executed)

### 7.1 Hypotheses

- H1: FIDL's mean utility at λ=0.1 exceeds BEST-FIXED on a fresh untouched confirmation set with paired 95% CI lower bound >0.
- H2: LCB abstention reduces wrong-action rate on near-tie items relative to direct GBT without reducing mean utility.

### 7.2 Baselines and ablations

B0, B1, B2, B3, REF; BEST-FIXED and MAJORITY selected on FIT only; SIMPLE-FEAT; direct GBT argmax; no-LCB direct evaluation; no-shift-gate; RANDOM and shuffled-label controls. Ablations: F0/F1, linear/GBT, LCB on/off, B1-vs-B2 deferral target, and shift gate on/off.

### 7.3 Data separation

Existing BANK/FIT/TUNE can be used only for fitting and predeclared calibration. The opened LEVAL is not used for selection, calibration, or a new independent confirmation. A new final confirmation set requires separate Planner approval, exact revision, ordered IDs and hashes, exact/normalized overlap checks, and contamination caveats. No MATH-500. Any dataset candidate is only a proposal and confers no access or experiment authorization.

### 7.4 Statistics

- The sole primary confirmatory contrast is FIDL − BEST-FIXED on the new confirmation set: per-item utility at λ=0.1, paired percentile bootstrap 95% CI, 10,000 resamples, type-7, locked seed, requiring lower bound >0. A single primary contrast needs no multiplicity adjustment.
- MAJORITY, SIMPLE-FEAT, direct GBT, and no-LCB form a predeclared secondary mechanism family; use Holm adjustment within that family. RANDOM and SHUFFLE are diagnostics, not primary superiority gates. Exact McNemar is only a secondary binary-accuracy diagnostic.
- SHUFFLE retains its unconditional denominator of 1,000 and separate F0-NO-GO/invalid/valid accounting. Fewer than 950 valid F1 replicates makes that diagnostic INCONCLUSIVE; it neither proves nor disproves the direct primary contrast and must not be relabeled PASS.
- Direct policy-difference confidence bounds for FIDL include support, effective sample size, and interval width. Missing/invalid required output ⇒ INCOMPLETE/INVALID.

### 7.5 Power and sample size

Prior discordance (16.7–22.7%) is only a planning reference, not an estimate for the new set. At n=300 it corresponds to roughly ±4.6–5.3pp accuracy-scale half-width, with wider utility intervals due to token variance. This is a learnability screen with uncertain power; no detection guarantee. Prefer ≥500 confirmation items if governance permits.

### 7.6 Proposed budget (not consumed)

- Backbone: same locked Qwen2.5-1.5B revision and deterministic decoding as R1.
- GPU: ≤1.0 aggregate GPU-hour, 55-minute inference wall fail-safe, 60-minute hard cap, NVML sampling every 10 s. Report wall and active separately.
- CPU analysis: two-replicate smoke first; full shards only if measured cost is acceptable. Proposed timeout 4 CPU-hours with checkpoints every 10 replicates; timeout means INCONCLUSIVE/INCOMPLETE, not PASS.
- No new model/API calls for permutation replicates; only frozen per-config outcomes are used.

### 7.7 Stop and continuation rules

Stop on support failure, data/lock inconsistency, missing/invalid primary outputs, primary CI lower bound ≤0, or budget breach. Continue only if the primary contrast passes and FIDL also beats direct GBT and no-LCB under the Holm-adjusted secondary family. Fewer than 950 valid SHUFFLE replicates leaves that secondary diagnostic INCONCLUSIVE but does not convert a valid primary result into either PASS or NO-GO. A positive point estimate without the required CI is not a pass. No threshold or endpoint changes after inspecting results.

### 7.8 Integrity requirements

Commit locks before inference; retain raw completions, per-item tokens/correctness, selection artifacts, seeds, NVML samples, per-replicate logs, and independent recomputation. No post-hoc editing, selective reruns, or hidden failures.

## 8. Planner questions

1. Is FIDL's full-information LCB formulation sufficiently different from safe policy improvement and direct policy-difference confidence sequences to justify a new preflight?
2. Should FCC be considered only as an alternative if FIDL's support/utility estimates are too weak, or is its shift guarantee too limited?
3. Is RRC too close to Adaptive-Solver to merit independent study?
4. Is there any defensible role for EC-RuleSearch, or should EC be explicitly abandoned for this problem?
5. Which new confirmation set, if any, is authorized for independent review? No access is granted by this document.

## 9. Actual resource use and unresolved evidence gaps

- This R8 round used **0 GPU-hours, 0 inferences, 0 API calls, 0 new experiments, and 0 CPU preflight**. Only read-only analysis of existing records and prior literature was performed.
- Evidence gaps: no fresh confirmation set, no full-information out-of-sample estimate, no validated shift detector, no EC necessity demonstration, and no cleared novelty for any candidate.
- R7 and R1 artifacts remain unchanged. This document is a proposal awaiting Planner R9 review, not an implementation authorization.
