# Phase-2 R7 Method Research — Failure Mechanism, Literature Audit, and New Proposals

Date: 2026-10-28
Status: **R7_RESEARCH_PROPOSAL_READY_FOR_PLANNER_REVIEW**. This is a read-only research proposal, not an experiment or an implementation authorization.

## 1. Current state and evidence sources

The R6 Planner decision (`planner/phase2_pilot_planner_decision_r6.md`) is authoritative: the current TACC/GBT-F1 route is stopped, results are frozen, and no further experiment is authorized. This document does not reopen it.

Preserved facts (all independently rechecked from the actual artifacts):

- 5,000 completed generations, zero failed generations; model `Qwen/Qwen2.5-1.5B-Instruct`, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- CANDIDATE: accuracy 0.633333, utility 0.6279553.
- B2/BEST-FIXED: accuracy 0.650000, utility 0.6410255.
- B1/MAJORITY: accuracy 0.640000, utility 0.6371011.
- SIMPLE-FEAT: accuracy 0.640000, utility 0.6345941.
- All three paired fixed/simple utility contrasts have 95% CIs spanning zero and negative point estimates: −0.0130702, −0.0091458, and −0.0066388.
- SHUFFLE: 749 F0-NO-GO, 251 valid F1-scored, 0 invalid, 0 errors; 251 < 950, so `INCONCLUSIVE_NULL` remains the only correct status. It is not a success and not proof that all adaptive controllers fail.
- Resource records: GPU inference wall 787.8377 s, NVML active integral 329.0410 s = 0.0914003 GPU-hours; permutation wall 13,692.4471 s and 523,065.4217 CPU-seconds.
- Lock SHA-256 remains `ff6c703e4dce45e88b6847a144433479a1702feae5cf5afc3a466ffd8a5c5035`.
- R6 explicitly prohibits rerunning inference, adding permutations, changing thresholds/model grids, or reusing the opened LEVAL for another candidate.

Evidence used: `final_stats.json`, `frozen_selection.json`, `null_0001_1000.json`, `derived_manifest.json`, `results/stage1/run_manifest.json`, `inference.log`, `inference_resume.log`, `inference_resume2.log`, `planner/pilot_result_verification.log`, `status.json`, and the new diagnostic `planner/r7_evidence_summary.json`.

## 2. What the current controller actually does

### 2.1 Features and target

- F0 has two surface features: Unicode-codepoint question length and numeric density (`src/phase2/features.py:135-174`). F1 appends a frozen 384-dimensional `HashingVectorizer` embedding (`src/phase2/features.py:29-49,177-195`). No answer/outcome information enters features.
- The utility is `u_i(c) = correct_i(c) − λ(prompt_i(c)+completion_i(c))/10000`, λ=0.1 (`src/phase2/stats.py:40-45`). One percentage point of accuracy costs 1,000 tokens. This is not total deployment cost: it excludes controller training, embedding computation, permutation analysis, and downstream execution overhead.
- Each non-B1 action regresses `u_i(c)−u_i(B1)` with ridge, multinomial logistic, or GBT; B1 is anchored to zero (`src/phase2/policy.py:176-214`). Selected model is GBT with 100 trees and depth 1. The selected action is argmax of predicted score if score > δ and shift score ≤ τ, otherwise B1 (`src/phase2/policy.py:133-147`).

### 2.2 Selection, thresholds, and fallback

- FIT 5-fold cross-validation compares candidate classes by **mean realized utility of selected actions**, not by Δu-R² (`src/phase2/policy.py:218-261`). F0/F1 are weighted equally, so feature choice is not made in FIT.
- Full-FIT models are then fitted for F0 and F1. TUNE selects feature set, δ∈{0,0.005,0.01,0.02}, and τ from TUNE shift-score percentiles 90/95/99 by realized utility (`src/phase2/policy.py:264-296`). Ties prefer F0, then smaller δ, then smaller τ.
- `ShiftDetector` standardizes each feature dimension with FIT mean/std and uses the mean Euclidean distance to the ten nearest FIT items in that space (`src/phase2/features.py:217-250`). It is a feature-space distance, not a validated distribution-shift detector.
- BEST-FIXED is the fixed configuration with highest FIT mean utility; MAJORITY is the most frequent per-item best action on FIT (`src/phase2/policy.py:299-323`).
- If TUNE selects F0, the run stops `NO-GO_IDENTICAL_TO_SIMPLE-FEAT` before LEVAL because CANDIDATE would be identical to the simple-feature comparator (`src/phase2/policy.py:375-378`). SIMPLE-FEAT uses the same model class/hyperparameters but an independent F0-only threshold selection (`src/phase2/policy.py:326-342`). CANDIDATE and SIMPLE-FEAT therefore differ in feature set and independently selected δ/τ, not in the model family or target.

### 2.3 Actual action-allocation failure

From `final_stats.json` and the new confusion diagnostic (`planner/r7_evidence_summary.json`):

- Hindsight best actions on LEVAL are B1=160, B0=96, B3=17, REF=18, B2=9.
- CANDIDATE chooses B1=135, B2=106, B3=30, REF=25, B0=4. In particular, when B0 is actually best (96 items), CANDIDATE chooses B0 only 2 times; it chooses B2 32 times and B1 43 times. When B2 is actually best (9 items), CANDIDATE chooses B2 only 3 times.
- The hindsight oracle upper bound is 0.8207188, while B2 is 0.6410255 and CANDIDATE is 0.6279553. There is large potential headroom, but no evidence that current features can realize it. This is not a “nothing to learn” result; it is an **action-value identifiability problem**, not proof that the action space lacks value.

## 3. Failure diagnosis, with evidence strength

### A1. State representation is insufficient

- **Support:** F1 does not beat SIMPLE-FEAT on utility (0.6279553 vs 0.6345941; CI [−0.0466694, 0.0331997]). The best action is not stable across items, and the candidate selects B2 far more often than B0, suggesting poor discrimination of when direct answering suffices.
- **Against:** The observed failure does not identify which missing property is needed. Better embeddings may exist, and F1 still selects F1 rather than F0, so it is not proven useless.
- **Unknown:** Whether semantic reasoning-pattern features, solution-step structure, domain/difficulty cues, or better encoders would change outcomes.
- **Minimum validation:** a predeclared representation ablation on untouched data, comparing F0, the current 384-d hash embedding, and one independently specified richer encoder with no outcome-dependent fitting. Do not add features until after seeing fresh outcomes.

### A2. Action values are not identifiable from current features

- **Support:** The median best-vs-second utility gap is 0.002135 on LEVAL; 89% have gap <0.05 and 85% have gap <0.005. This is near-tie noise for a hard argmax. Yet hindsight upper bound 0.8207 is much higher than fixed B2 0.6410, so the action space has potential value. Candidate misallocations are concrete evidence of wrong choices.
- **Against:** Large gaps do exist in a minority of cases, and B1 is majority best in 160/300. Some configurations are consistently preferred, so “no signal” would be too strong.
- **Unknown:** Whether the observed differences are predictable from question features or are mostly generation/estimation noise. The gap distribution alone cannot separate those explanations.
- **Minimum validation:** cross-fitted prediction of **pairwise utility differences** with shuffled-label and feature-only controls. A positive out-of-sample difference above best fixed is required, not just classification accuracy or an oracle gap.

### A3. Decision mechanism is inappropriate for near-ties

- **Support:** Hard argmax plus a fixed δ and τ can convert small estimation errors into systematic wrong actions; there is no probability calibration or risk guarantee. The candidate’s deferral to B1 does not prevent it from choosing B2 in many cases where B2 is not best.
- **Against:** Deferral is a valid design in principle, and B1 is not a bad fallback: its utility is 0.6371, only 0.0039 below B2. Hard switching is not proven to be the main cause.
- **Unknown:** Whether confidence-aware abstention, soft selection, or residual cascade would outperform hard argmax without increasing variance.
- **Minimum validation:** compare hard argmax to confidence-gated abstention and a randomized/soft policy at matched inference cost, with confidence intervals and deferral-rate reporting.

### A4. Generalization mechanism is weak

- **Support:** `ShiftDetector` measures only feature-space distance to FIT items. It has no demonstrated OOD detection accuracy, no calibration guarantee under semantic shift, and no evidence of improving utility on a new distribution. The selected τ=27.1665 is a percentile choice on TUNE, not a validated shift threshold.
- **Against:** A shift detector need not be perfect to be useful, and no dedicated shift experiment was run, so “it fails at OOD detection” is unproven.
- **Unknown:** Actual behavior on temporal/domain/backbone shifts and whether a calibrated abstention would be safer.
- **Minimum validation:** untouched temporal/domain holdout with predeclared shift metrics (defer rate, coverage, utility), not just distance distributions.

### A5. Objective function is incomplete rather than wrong

- **Support:** The token penalty captures generation cost but omits controller training, embedding, and large analysis costs. The permutation phase alone consumed 523,065 CPU-seconds, which is not included in deployment utility. B1’s much lower token use (86,968 vs CANDIDATE 161,341) makes the omission material.
- **Against:** If the intended objective is specifically accuracy–generation-token trade-off, the formula is well-defined and not inherently flawed. λ=0.1 is explicitly exploratory-informed, not a deployment-optimal price.
- **Unknown:** Whether a fuller cost model would change the preferred action or simply confirm that the controller is uneconomical.
- **Minimum validation:** separately meter controller CPU/GPU/latency and include it in a secondary total-cost analysis; do not retroactively redefine the primary endpoint to rescue results.

### A6. Evaluation and model-selection issues

- **Valid-replicate scarcity:** 749/1000 replicates selected F0 and were not scored. The gate required ≥950 valid F1 scores but only 251 remained. This is a post-selection conditional estimand, not a clean unconditional null; it cannot establish learnability or its absence.
- **LogisticRegression convergence warnings:** warnings at max_iter=1000 indicate optimization/conditioning limitations in that candidate family. They do not invalidate the selected GBT, but they constrain what the grid can claim and must be disclosed. They are not evidence that all model classes are poor.
- **Initial execution failures:** missing analysis directory and a stage-input length mismatch were engineering defects, not negative scientific results. They were recovered deterministically and preserved in logs; they increase the need for audit tests but do not change the numerical outcomes.
- **Minimum validation:** preserve these limitations, use a predeclared replicate validity rule and full-pipeline validity counts, and do not alter the 950 threshold or repeat LEVAL to make them disappear.

## 4. What SHUFFLE means—and does not mean

- 749 replicates selected F0 and were not scored, 251 selected F1 and were scored, and 0 were invalid. With only 251 valid scores, the required ≥950 condition fails, hence `INCONCLUSIVE_NULL`.
- This does **not** show that adaptive selection is futile; it shows the protocol cannot make a valid confirmatory judgment under the frozen rule. Nor does it show superiority: the fixed/simple contrasts independently failed.
- RANDOM passing does not rescue those failures or make SHUFFLE a pass.
- Valid F1 is itself a selection event, so the 251 scores are conditional on that event. They cannot be treated as an unrestricted permutation distribution. Selecting or recalibrating δ/τ from those results would be another leakage path.
- No additional replicates, threshold edits, or post-hoc null reinterpretation are permitted. A future design needs a preregistered way to handle F0 selection and enough valid scores, not a reinterpretation of this one.

## 5. Literature audit

The table distinguishes paper-reported facts from my analysis and new proposals. All entries were checked against primary full texts unless explicitly marked otherwise.

### 5.1 Routing, cost, and adaptive inference

| Work | Actual mechanism and reported evidence | Limitation / what remains for TACC |
|---|---|---|
| **RouteLLM**, Ong et al., ICLR 2025, [arXiv:2406.18665](https://arxiv.org/abs/2406.18665) | Bradley–Terry/preference router between strong and weak LLMs; cost = fraction of strong calls. Best augmented MT Bench APGR 0.802 vs random 0.500, CPT(50%) 13.40% vs 49.03%; MMLU 0.603, GSM8K 0.622. Arena-only transfers poorly; in-domain augmentation is necessary. | It is model-pair routing, not same-backbone scaffold selection. Pairwise preference fitting is worth ablating, but it does not solve complementarity, OOD abstention, or paired utility evaluation. Novelty for “predict baseline win and threshold” is untenable. |
| **FrugalGPT**, Chen et al., TMLR 2024, [arXiv:2305.05176](https://arxiv.org/abs/2305.05176) | Learned service ordering + post-generation DistilBERT scorer + threshold cascade, optimizing accuracy subject to expected USD budget. HEADLINES cost $33.1→$0.6 (98.3% saving); OVERRULING $9.7→$2.6; COQA $72.5→$29.6; AGNEWS $64.6→$15.9; SCIQ $132.4→$63.1. | Cascade is post-answer and can invoke multiple generators; it is not B1 fallback. MPI pruning can become a complementarity audit, but an upper bound does not make it predictable. Cost is task/API-specific, and CIs are absent. |
| **Route to Reason**, Pan et al., WWW 2026, [DOI 10.1145/3774904.3792556](https://doi.org/10.1145/3774904.3792556), [arXiv:2505.19435](https://arxiv.org/abs/2505.19435) | Frozen mpnet query embedding plus learned model/strategy embeddings; supervised BCE correctness and MSE length heads, then cost-aware argmax. Overall OOD accuracy 81.7% vs QwQ 82.3%; ID 82.5 vs 80.0. LiveCodeBench 34.6 vs 39.5. | Absolute correctness and output length, not B1-relative utility. Joint model+strategy routing and dual heads are already occupied. Two-head decomposition is useful only if it produces calibrated net utility, not another coarse routing table. |
| **Adaptive-Solver**, Zhou et al., IPM 2025, [DOI 10.1016/j.ipm.2024.104052](https://doi.org/10.1016/j.ipm.2024.104052), [arXiv:2310.01446](https://arxiv.org/abs/2310.01446) | Heuristic multi-round cascade over model, sample size, prompting, and decomposition, triggered by answer consistency. GSM8K 92.49% vs 87.93%; SVAMP 90.75% vs 88.75%; 46–85% lower API cost but 1.45× inference time. | Residual wrong-set complementarity is useful, but per-dataset validation pipelines have no OOD guarantee and agreement is not correctness. A residual cascade can be evaluated but not presented as new. |
| **Chen et al.**, NAACL Findings 2025, [ACL](https://aclanthology.org/2025.findings-naacl.200/) | BERT router over five augmentation classes: self-knowledge, direct, CoT, rewrite, RAG. Correct-then-fastest labels and TCA/TAI. MMLU-STEM EM 78.63 vs CoT 65.34; AmbigNQ 56.85 vs QE 49.20; Hotpot 50.90 vs rewrite 44.60. | No OOD fallback or calibrated abstention; fastest-correct labels inherit latency noise. “Beyond ability” is not a shift detector. Utility-aware confidence-aware labels are the only defensible improvement, not a new router archetype. |
| **Adaptive-RAG**, Jeong et al., NAACL 2024, [ACL](https://aclanthology.org/2024.naacl-long.389/), [arXiv:2403.14403](https://arxiv.org/abs/2403.14403) | T5 classifier chooses no/single/multi-step retrieval by complexity; simplest correct strategy wins. Across six datasets FLAN-T5-XL Adaptive-RAG 37.17 EM / 46.94 F1 / 42.10 Acc vs single-step 34.83/44.31/38.87; multi-step 39.00/48.85/43.70 with more steps/time. Classifier accuracy 54.52%. | Complexity is outcome/backbone-dependent, labels can be wrong, no all-fail abstention, no OOD evaluation. Oracle-router diagnostic is useful to bound headroom, not as a new claim. |

### 5.2 Deferral, selective prediction, and uncertainty

| Work | Actual mechanism and reported evidence | Limitation / what remains for TACC |
|---|---|---|
| **Mozannar & Sontag**, ICML 2020, [PMLR](https://proceedings.mlr.press/v119/mozannar20b.html), [arXiv:2006.01862](https://arxiv.org/abs/2006.01862) | Cost-sensitive learning to defer to an expert, with a deferral logit and consistent surrogate. CIFAR-10 gain 1.01pp over Confidence; CIFAR10H system accuracy 96.29±0.25 vs 95.09±0.40. | It concerns model-vs-human/expert, not B1 fallback or token utility. Consistency is asymptotic, not finite-sample or shift validity. A joint cost-sensitive action model is worth trying, not a new L2D claim. |
| **Liang, Peng & Sun**, TMLR 2024, [arXiv:2405.05160](https://arxiv.org/abs/2405.05160) | Post-hoc selective classification under ID/covariate/label shift using raw-logit/geometric margins and AURC. ImageNet-EVA both shifts, conf-M 0.34/1.20/5.43 and KNN 1.24/2.98/7.16 (×10⁻²). | Margins are not calibrated probabilities, and threshold/calibration selection remains unsolved. Top-two action margins can be diagnostics, not proof of better fallback or shift-valid risk control. |
| **Fang & Nalisnick**, TMLR 2026, [correct OpenReview](https://openreview.net/forum?id=SZQJ8K2DUe) | Split-conformal covers expert correctness, with abstain/consensus/human-preferred/model-preferred routes. At nominal 90% CP, OvA/CIFAR-10 achieved ~87% and average set size 1.07; abstention/consensus gained ~2–5pp but coverage fell 8–38 points. | CP covers correctness, not Bayes allocation or utility regret. Shift still breaks calibration. A conformal deferral set for “beats B1 by >δ” is close, but multi-action selection and shift require separate treatment. |
| **Tan, Rangwala & Maddix**, arXiv 2026, [arXiv:2610.02487](https://arxiv.org/abs/2610.02487) | Threshold-aware conformal routing from cheap surrogate to expensive simulator: invoke when calibrated interval crosses τ; threshold-local width shaping. At 90% nominal coverage, simulation rates CircuitNet 46.4→11.6%, AirfRANS 19.8→7.4%, ShapeNet-Car 46.4→34.7%; four of six lowest. | Marginal, not conditional coverage; scalar threshold only, no LLM or shift detector. Calibrating utility-gain lower bounds is a useful analogy, not a new routing method by itself. |

### 5.3 Counterfactual action-value estimation

| Work | Actual mechanism and reported evidence | Limitation / what remains for TACC |
|---|---|---|
| **Dudík, Langford & Li**, ICML 2011, [arXiv:1103.4601](https://arxiv.org/abs/1103.4601) | Doubly robust estimator combines regression with inverse-propensity residual weighting; DR RMSE lower than IPS on 7/9 UCI sets and improves DR-learned classifiers on all 9. | DM + argmax is TACC’s current approach, not DR. DR needs overlap and correct nuisance separation; it cannot identify never-observed actions or cure hidden confounding. |
| **Jiang & Li**, ICML 2016, [PMLR](https://proceedings.mlr.press/v48/jiang16.html), [arXiv:1511.03722](https://arxiv.org/abs/1511.03722) | Sequential DR, two-fold cross-fitting, and safe policy improvement via `value − C·stddev`; DR often beats IS/WIS and improves with cross-fitting. | TACC is one-step, so Bellman recursion is unnecessary. The useful piece is held-out LCB-based deferral; that is already prior art and cannot be claimed as new. |
| **Waudby-Smith et al.**, JDS 2024, [DOI 10.1145/3643693](https://doi.org/10.1145/3643693), [arXiv:2210.10768](https://arxiv.org/abs/2210.10768) | Anytime-valid DR pseudo-outcomes and betting confidence sequences for direct policy-value differences under adaptive logging. Results are theoretical/synthetic, not real benchmarks. | Direct policy-difference CSs are highly relevant but already occupied. Positivity and exchangeability are required; post-hoc target selection is not solved. A “DR anytime router” would collide without a new selection mechanism. |

### 5.4 Evolutionary and agent-architecture search

| Work | Actual mechanism and reported evidence | Limitation / what remains for TACC |
|---|---|---|
| **ADAS / Meta Agent Search**, Hu et al., ICLR 2025, [arXiv:2408.08435](https://arxiv.org/abs/2408.08435) | LLM meta-agent writes full agent `forward` code into an archive; validation fitness only. DROP 79.4 vs 65.8 F1, MGSM 53.4 vs 39.0, MMLU 69.6 vs 65.9, GPQA 34.6 vs 31.6. Reported search costs about $500 ARC/$300 reasoning. | It evolves workflows, not compact routers, and has no EC necessity proof for TACC. Archive diversity is useful, but elite selection on small validation sets amplifies overfitting. |
| **AlphaEvolve**, Novikov et al., DeepMind 2025, [arXiv:2506.13131](https://arxiv.org/abs/2506.13131) | LLM diff/code evolution with MAP-Elites/island archives and evaluation cascades. Rank-48 4×4 complex matrix multiplication, 0.7% Borg compute recovery, 23% tiling speedup, 32% FlashAttention-kernel speedup. Includes a no-evolution ablation. | It provides the clearest reason to require no-evolution controls. Reliable execution feedback, not LLM evolution per se, is the differentiator. No evidence it solves small noisy utility landscapes. |
| **AgentSquare**, Shang et al., ICLR 2025, [arXiv:2410.06153](https://arxiv.org/abs/2410.06153) | Modular Planning/Reasoning/Tool/Memory search with LLM recombination, module evolution, and surrogate screening. Scores 0.607/0.695/0.781/0.524/0.583/0.669 on six environments; recombination ablation changes some tasks, including no PDDL change. | It is whole-agent search, not per-query routing, and does not show searched-agent transfer. Surrogate screening can induce selection bias. Typed controller components may be borrowed, not claimed novel. |
| **MaAS**, Zhang et al., ICML 2025, [PMLR](https://proceedings.mlr.press/v267/zhang25bi.html), [arXiv:2502.04180](https://arxiv.org/abs/2502.04180) | Query-conditioned probabilistic agentic supernet with early exit and cost-aware Monte Carlo updates. Average 83.59 vs AFlow 82.25; MATH training $3.38 vs $22.50 and inference $0.42 vs $1.66. Cross-model and cross-dataset gains. | Closest prior art for cost-aware per-query architecture selection and early exit. It uses stochastic multi-agent workflows and operator editing, not fixed B0/B1/B2/B3/REF. A B1 early-exit is worth testing, not a novelty claim. |

## 6. Candidate methods

The candidates are ordered by expected mechanism fit and by how directly they address the observed value-estimation failure, not by presumed novelty.

### Candidate 1 — **RCDR: Residual-Corrected Doubly Robust Router with baseline-relative LCB abstention**

**Precise question.** Can cross-fitted, support-valid counterfactual estimates of per-action utility differences prevent near-tie estimation errors from turning into systematic wrong configuration choices?

**Current defect.** Current GBT is direct-method argmax on noisy Δu, with no counterfactual residual correction or safe-selection guarantee. The 89% near-tie rate makes this failure plausible.

**Mechanism.**

1. For each action \(a\), fit a nuisance utility model \(\hat m_a(x)\) on one training fold. On the held-out fold, compute for each candidate policy \(\pi\):
   \[
   z_i(\pi)=\sum_a\pi(a\mid x_i)\hat m_a(x_i)
   +\frac{\pi(A_i\mid x_i)}{h(A_i\mid x_i)}\{U_i-\hat m_{A_i}(x_i)\}.
   \]
   Estimate \(\Delta(\pi,\pi_0)=\mathrm{mean}[z_i(\pi)-z_i(\pi_0)]\) with a direct paired-difference confidence bound. Deploy only if the lower bound exceeds the preregistered margin; otherwise use B1. Evaluate B2 as the primary comparator as well as B1.
2. Require action support: \(\pi(a\mid x)>0\Rightarrow h(a\mid x)>0\). If support fails, return NO-GO. Use cross-fitting for both nuisance model and candidate policy; no fitting on LEVAL.
3. Deferral is based on a one-sided utility-gain bound, not a point estimate. Report width, support, effective sample size, and whether DR widened or narrowed intervals.

**Existing pieces vs new combination.** DM/DR, safe policy improvement, and direct policy-difference confidence sequences already exist. The potentially new combination is *support-valid, baseline-relative counterfactual utility routing with an explicit B1 cost floor and a shift-aware abstention rule for a frozen LLM’s scaffold configurations*. That combination is **NOVELTY_UNRESOLVED** until a fresh audit confirms no prior same-target work. It is not a claim that DR itself is new.

**Falsifiable tests.**

- H1: on untouched confirmation data, RCDR’s mean utility exceeds BEST-FIXED with paired CI lower bound >0. If it fails, H1 is rejected.
- H2: compared with direct GBT argmax, RCDR reduces wrong-action rate on near-tie items without reducing total utility. If utility does not improve, H2 is rejected.
- H3: DR does not necessarily reduce variance; if intervals widen or support fails, the mechanism is rejected, not rescued.
- Simple controls: direct GBT, B1, B2, SIMPLE-FEAT, MAJORITY, RANDOM, shuffled labels, direct (non-DR) counterfactual evaluation, and no-shift-gate ablation.

**Expected failure modes.** Lack of support, severe inverse-propensity weights, direct-model misspecification, wider CIs, or no learnable advantage. Any of these must stop the method, not trigger more tuning.

**EC necessity.** None. The problem is statistical estimation, not a large search landscape. EC would be decoration here.

### Candidate 2 — **SCC: Shift-Calibrated Conformal Abstention for utility gain**

**Precise question.** Can a distribution-free, one-sided utility-gain calibration provide a reliable abstain-to-B1 decision when utility differences are noisy and distribution shift is present?

**Current defect.** Hard δ/τ choices are heuristic; shift distance alone has no risk guarantee.

**Mechanism.**

1. On FIT, compute per-action gain \(G_a=U_a-U_{B1}\). On a separate calibration split, fit split-conformal lower bounds for \(G_a\) using a one-sided nonconformity score. Deploy \(a\) only if its lower confidence bound exceeds δ=0.01; otherwise B1. For multi-action selection, predeclare a max-statistic/intersection–union rule rather than selecting the best-looking CI after inspection.
2. Use threshold-local width shaping from TACR only as an optional ablation, not as a claim of novelty. Calibrate on TUNE; freeze δ/τ and score construction before LEVAL.
3. Under shift, do not claim conformal validity: report calibration/test exchangeability diagnostics and defer more often. If the shift diagnostic fails, the run is INCONCLUSIVE, not a pass.

**Existing pieces vs new combination.** Conformal deferral, threshold-aware conformal routing, and selective classification under shift already exist. The possible new combination is *one-sided continuous token-utility-gain calibration with B1 as the explicit cost floor and multi-action intersection–union selection for frozen-LLM scaffolds*. That is **NOVELTY_UNRESOLVED** because it may be seen as an application of known CP to a new label type, not a new algorithm.

**Falsifiable tests.**

- H1: SCC yields a lower-bound utility above B1 while preserving the predeclared coverage/risk target on held-out calibration data. If empirical coverage is invalid, reject.
- H2: SCC has fewer harmful switches than direct argmax at equal utility. If abstention does not help, reject.
- H3: under induced shift, SCC must not outperform an uncalibrated gate while claiming validity; if it does, the claim is rejected.
- Controls: B1, B2, direct GBT, no-conformal threshold, TACR-style scalar-threshold baseline, and shuffled calibration labels.

**Expected failure modes.** Exchangeability violation, uninformative wide intervals, excessive abstention, no coverage under shift, or no advantage over B2.

**EC necessity.** None. Split-conformal calibration is deterministic and cheap; EC cannot create the missing guarantee.

### Candidate 3 — **EC-RuleSearch: Pareto search over typed controller rules with no-evolution controls**

**Precise question.** If a combinatorial rule landscape is genuinely too large for exhaustive enumeration, can heredity outperform random search and direct greedy rule induction at equal real-evaluation budget?

**Current defect.** There is no evidence that current search is inadequate; adding evolution now would amplify selection bias rather than fix value estimation.

**Mechanism.**

1. Genome: a small typed rule grammar containing utility-estimator type, feature-set choice, δ, τ, fallback action, and optional residual-cascade order. The grammar must be shown to exceed practical enumeration before EC is considered.
2. Fitness: cross-fitted mean utility gain over B1 and B2, plus a complexity penalty, support validity penalty, and a paired-uncertainty penalty. Evaluation uses the same preregistered paired data and no LEVAL-based search.
3. Selection: MAP-Elites archive with descriptors for deferral rate, action coverage, and shift regime. Mutations change one typed component; crossover swaps utility-estimator and gating blocks. Every candidate uses the same deterministic evaluation and confidence-bound rule.
4. Mandatory controls: exhaustive enumeration where feasible, random search, local greedy rule induction, no-archive, no-recombination, and repeated independent LLM proposals at equal real-evaluation/token budget. If EC does not beat those controls, it is rejected.

**Existing pieces vs new combination.** ADAS, AlphaEvolve, AgentSquare, and MaAS already cover code/workflow/supernet evolution. The only defensible combination is *a typed, uncertainty-aware rule search with direct fixed/simple baselines and an explicit no-evolution control for frozen-LLM configuration selection*. That is **NOVELTY_UNRESOLVED**, and EC itself remains unjustified unless the combinatorial-landscape and heredity-benefit tests pass.

**Falsifiable tests.**

- H1: EC finds a rule with better held-out utility than direct GBT and random search at equal budget. If not, EC is unnecessary.
- H2: archive/recombination outperforms no-archive/no-recombination and repeated independent proposals at equal budget. If not, the archive is unnecessary.
- H3: a small grammar can be enumerated; if exhaustive search is as good, EC is rejected.

**Expected failure modes.** Overfitting to validation, no heredity benefit, better random/greedy baselines, or no complementarity. Any of these stops EC.

**EC necessity.** Conditional, not presumed. It is justified only by demonstrating a genuinely combinatorial landscape and heredity benefits under equal-budget controls. Otherwise use direct enumeration or the first two candidates.

## 7. Ranking rationale

1. **RCDR** is first because it directly attacks the most concrete observed defect: near-tie utility estimation and safe selection, while requiring explicit support, cross-fitting, and a stop-on-no-signal rule. It can return a defensible nondeployment result instead of forcing a controller.
2. **SCC** is second because it provides a different abstention mechanism with explicit coverage diagnostics and a clear shift-failure mode. It is less likely to address model misspecification and may be too conservative.
3. **EC-RuleSearch** is last and optional. Current evidence says the search is not the bottleneck. It should proceed only if a real combinatorial landscape and heredity benefit are demonstrated, with no-evolution controls.

No candidate is currently a validated algorithm or a cleared novelty claim.

## 8. Pre-registration draft for RCDR (not executed)

### 8.1 Hypotheses and primary endpoint

- **H1 (primary):** on a new untouched confirmation set, RCDR’s mean utility at λ=0.1 exceeds BEST-FIXED with a paired 95% bootstrap CI lower bound >0.
- **H2 (mechanism):** RCDR reduces wrong-action rate on near-tie items relative to direct GBT without reducing mean utility.
- Primary endpoint is utility, not raw accuracy. Raw accuracy, prompt tokens, completion tokens, Pareto, and controller overhead are mandatory separate outcomes and cannot be used to redefine a pass.

### 8.2 Baselines and ablations

- Fixed: B0, B1, B2, B3, REF; BEST-FIXED and MAJORITY selected on FIT only.
- Simple: SIMPLE-FEAT, RANDOM, shuffled labels, direct GBT argmax, direct (non-DR) counterfactual evaluation, and no-shift-gate.
- Ablations: DR vs no-DR, shift gate on/off, F0/F1, B1-vs-B2 deferral target, LCB vs point-estimate selection, support-validity on/off.

### 8.3 Data isolation

- Existing BANK/FIT/TUNE may be used only for nuisance/candidate fitting and calibration; the opened LEVAL is not reused for selection, calibration, or a new independent confirmation.
- A new final confirmation set requires separate Planner approval. Candidate options are only proposals, not authorizations: a locked, previously unused SVAMP train partition or another Planner-approved public math QA split. No MATH-500.
- Before any use, lock dataset revision, all item IDs, ordered hashes, exact/normalized overlap with GSM8K train/test and previous splits, and contamination caveats. Do not fetch, inspect answers, or infer before the lock is approved.

### 8.4 Statistics

- Per-item utility at λ=0.1, paired percentile bootstrap 95% CI (10,000, type-7, seed locked), exact McNemar only as secondary accuracy evidence, and SHUFFLE/RANDOM mid-rank ≥0.95.
- D2 remains intersection–union: BEST-FIXED, SHUFFLE, RANDOM, MAJORITY, and SIMPLE-FEAT must all pass. Valid F1 replicates ≥950. Any missing/invalid required output makes the run INCOMPLETE/INVALID.
- Direct paired policy-difference CIs for RCDR, with support/effective-sample-size and interval-width reporting. No post-hoc endpoint or threshold changes.

### 8.5 Power and sample size

Use the observed discordance scenarios only as planning references: q=16.7–22.7% on the prior public benchmark, corresponding to roughly ±4.6–5.3pp accuracy-scale half-width at n=300. Utility CIs may be wider due to token variance. Treat the first study as a learnability screen with uncertain power, not as a guaranteed ±2–3pp detector. Prefer ≥500 confirmation items if data governance permits, without changing the scientific question.

### 8.6 Budget (proposal, not consumed)

- Backbone: same locked Qwen2.5-1.5B revision and decoding as R1.
- GPU: at most 1.0 aggregate GPU-hour, 55-minute inference wall fail-safe and 60-minute hard cap; NVML 10-second sampling and separate wall/active accounting.
- CPU analysis: 2-replicate smoke test first, then full shards only if measured cost is acceptable. Proposed timeout 4 CPU-hours, checkpoint every 10 replicates; any timeout is INCONCLUSIVE/INCOMPLETE, not PASS.
- No new model/API calls for permutation replicates; use frozen per-config outcomes only.

### 8.7 Stop and continuation rules

- Stop on support failure, missing data, nonreproducible lock, missing/invalid outputs, valid F1 <950, or any breach of budget.
- Continue only if all five D2 contrasts pass, plus the direct GBT and no-DR comparisons show the mechanism’s contribution. A positive point estimate without the required CI is not a pass.
- If direct GBT fails the gate, RCDR cannot be described as a rescue. If RCDR fails, stop; do not tune against the confirmation set.

### 8.8 Integrity and reproducibility

- Commit locks before inference; preserve source/partition/subset hashes, full raw completions, per-item tokens and correctness, selection artifacts, seeds, NVML samples, and per-replicate logs.
- Independent recomputation must confirm metrics and gate outcomes. No post-hoc result editing, selective reruns, or hidden error traces.

## 9. Open questions for Planner

1. Is the proposed support-valid RCDR combination sufficiently distinct from DR/safe-deferral literature, or should it be rejected as incremental?
2. Is a new confirmation partition (e.g., locked SVAMP train) acceptable after independent lock and contamination review, or must another untouched source be chosen?
3. Should SCC proceed as an alternative if RCDR’s support diagnostics are too weak?
4. Is there any justification for EC-RuleSearch, or should EC be explicitly abandoned for this problem?
5. Which candidate, if any, is authorized for a future preflight? No execution is authorized by this proposal.

## 10. Actual resource use and evidence gaps

- This R7 round used **0 GPU-hours, 0 model inferences, 0 API calls, and 0 new experiments**. The only new computation was read-only analysis of existing records and literature. No budget was consumed beyond existing R1 artifacts.
- Evidence gaps: no fresh untouched confirmation set, no support-valid counterfactual estimate, no validated shift detector, no EC necessity demonstration, and no cleared novelty for any candidate.
- All proposed methods, data choices, and future budgets are proposals awaiting Planner approval.
