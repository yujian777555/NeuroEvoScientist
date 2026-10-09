# When Does Task-Conditioned Cognitive Configuration Search Generalize?

## A Controlled Audit of LLM Agent Scaffolds with Fair Baselines, Token Costs, and a Cross-Benchmark Test

---

## Abstract

LLM agents are usually deployed with a fixed, hand-designed cognitive
configuration: a reasoning strategy, an episodic memory/exemplar policy, and
a context budget chosen once and reused across tasks. We ask a narrower and
more auditable question than "can we evolve better agents": do
task-conditioned choices of these configuration components materially change
accuracy and inference cost above a frozen backbone, and does automatic
search over them find configurations whose advantage survives fair baselines
and unseen data?

We study this with a three-tier audit of QA-style single-agent scaffolds
over frozen Qwen2.5 backbones, keeping every tier's evidence status
explicit. Tier 1 (previously locked, descriptive): on an untouched GSM8K
holdout, a search-selected chain-of-thought configuration outperformed four
fixed baselines that all used direct answering, by +29.0 percentage points
at 1.5B and +16.7 points at 7B — an architecture-matters result that
confounds search with the CoT-versus-direct gap and cannot be attributed to
search alone. Tier 2 (fair-baseline dev audit): against CoT-matched presets
on the reused GSM8K dev slice, the search-selected configuration ties the
strongest preset (60.0% vs 59.0%, p=1.0); its +10-point edge over a
no-memory CoT control is exploratory (p=0.087). Tier 3 (pre-registered
cross-benchmark confirmation): on 300 locked SVAMP test items never used
for search or tuning, the search-selected configuration scores 70.33%,
statistically indistinguishable from both the strong CoT preset (71.67%;
primary contrast −1.33pp, 95% CI [−6.00, +3.33], exact McNemar p=0.67) and
the no-memory control (70.33%; 0.00pp, p=1.0) — and the dev-side memory
benefit does not replicate. Cost analysis is equally blunt: the no-memory
control matches the searched configuration's observed accuracy with 1.75×
fewer total tokens. Equal-budget evolutionary search also does not beat
random search in our compact audited space, and a correctly implemented
trainable Mamba-2 substrate is not selected as beneficial.

Our contribution is not a new optimizer but a falsifiable audit protocol —
fair CoT-matched baselines, item-level paired statistics, total-token cost
accounting, and a pre-locked cross-benchmark confirmation — together with
its two-sided findings: cognitive configuration choices matter materially,
while search superiority and universal transfer of dev-side preferences are
unsupported.

---

## 1. Introduction

Assembling an LLM agent involves choices that are usually made by hand and
then frozen: whether to reason directly or step by step, whether to carry
an episodic memory of exemplars and in what form, and how much of the
context budget to spend on them. A growing line of work automates these
choices — searching agent programs, modular designs, or multi-agent
topologies — and typically reports that the searched artifact beats the
manual one on the benchmark used for searching. What is audited far less
often is whether such advantages survive two elementary controls: (i)
baselines matched on the *components* the search actually varies, and (ii)
evaluation on data the search never touched.

This paper reports such an audit for task-conditioned *cognitive
configuration search*: per-task selection of a reasoning strategy, an
episodic memory/exemplar policy, and a context allocation policy above a
frozen backbone. Our setting is deliberately modest — QA-style single-agent
scaffolds, not interactive tool-using or multi-agent systems, and not
neural architecture search over backbone weights — because the audit
questions we ask are already sharp there, and because leakage-safe paired
evaluation is feasible at that scale.

We organize the evidence into three tiers with explicitly different
epistemic status. **Tier 1** is a previously locked holdout study
(Phase-17–21 of the underlying project, frozen before this paper): its
headline — a searched configuration beating the strongest fixed baseline by
+29.0 percentage points at 1.5B and +16.7 at 7B on GSM8K holdout — is real
but descriptive, because all four fixed baselines used direct answering
while the searched configuration used chain-of-thought (CoT). The gap
therefore measures "architecture matters" more than "search helps."
**Tier 2** repairs the baseline fairness: seven CoT-matched presets
compared against the search-selected configuration on the same dev slices
the search used (exploratory by construction). **Tier 3** is a
pre-registered confirmation: three configurations locked before any
inference, evaluated once on the 300-item original SVAMP test split, a
public benchmark never used for search, calibration, or tuning.

The findings are two-sided. Configuration choices matter: reasoning
strategy alone swings GSM8K dev accuracy from 11% (direct) to 50–60% (CoT),
and prompt-token cost varies 10× across presets with similar accuracy. But
the search-selected configuration shows no detectable advantage over a
strong hand-picked CoT preset on either the dev slice or the locked SVAMP
test; its dev-side +10-point benefit over a no-memory control does not
replicate cross-benchmark (0.00pp, p=1.0); the cheapest control matches its
observed SVAMP accuracy with 1.75× fewer total tokens; and, in the compact
space where we enumerated the full landscape, equal-budget evolutionary
search does not outperform random search. We report all of this, including
the negative results, as the contribution: a protocol that makes
configuration-search claims falsifiable, and a precise map of which claims
survived it.

## 2. Related Work

**Automated agent design.** ADAS searches over agent programs expressed in
code; AgentSquare searches a modular design space of planning, reasoning,
tool-use, and memory modules; MaAS performs query-dependent multi-agent
architecture search through an agentic supernet and explicitly prices
inference resources. These systems optimize performance (MaAS also cost) on
the search distribution. We differ in target and in emphasis: our search
target is the internal cognitive configuration of a single frozen-backbone
agent (reasoning policy, episodic memory, context allocation), and our main
object of study is the gap between search-side selection and held-out,
fair-baseline, cross-benchmark evidence — including where the search
procedure itself fails to beat random search. Evo-Memory and related recent
work study continually evolving or self-updating agent memory during
deployment; in our setting memory is not evolved online — the memory policy
is one component of a task-conditioned configuration searched against a
fixed, calibration-only experience bank. DSPy compiles declarative LLM
programs into optimizable pipelines; EvoPrompt evolves prompt text. We
treat the reasoning strategy as one gene jointly audited with memory and
context policy rather than optimized in isolation.

**Scaffolds and prompting.** ReAct-style reasoning-acting loops, Reflexion,
and chain-of-thought prompting are hand-designed cognitive configurations
in our terms; verification and planning variants appear in our search space
as reasoning genes. Retrieval-augmented generation grounds LLMs in external
evidence; our memory policies manage a leakage-safe, calibration-only
exemplar bank, and we quantify when such memory helps, hurts, or is
neutral.

**Search methodology.** Our evolutionary loop follows regularized-evolution
and NSGA-II-style non-dominated sorting with crowding distance; Bayesian
optimization is the standard sample-efficiency reference; AlphaEvolve
shares the evolutionary loop but evolves programs. Unlike NAS over backbone
weights, our search operates above a frozen LLM, and — critically — we
enumerate the compact search space exhaustively so that evolutionary search
can be audited against equal-budget random search on a known landscape.
Mamba and Mamba-2 provide the selective state-space models from which our
trainable memory substrate was built; that substrate is implemented and
searchable but, as we report, not selected as beneficial.

**Evaluation.** We use GSM8K, SVAMP, PubMedQA, and QASPER (in its LongBench
form) with frozen Qwen2.5-Instruct backbones. We claim no priority over any
of the above; the contribution is the audit protocol and its two-sided
findings.

## 3. Setting and Audit Design

**Cognitive configuration space.** A configuration is a structured genome
over three gene families: (i) *memory policy* — none / recency / retrieval
(term-frequency cosine or hashed bag-of-words cosine over a calibration-only
exemplar bank) / a trainable Mamba-2 substrate / hybrid, with recall width
and exemplar count sub-genes; (ii) *reasoning strategy* — direct,
chain-of-thought (with depth), verify, planner; (iii) *context policy* —
full, truncated, or answer-only exemplar verbosity with word budgets.
Normalization removes semantically inactive sub-genes before hashing so
duplicate phenotypes are never double-counted. A compact audit layer
(memory × reasoning × context = 48 configurations) is fully enumerated per
benchmark to obtain a ground-truth landscape.

**Three evidence tiers.** Because the audit's credibility depends on not
mixing evidence of different status, we keep three tiers separate
throughout:

- **Tier 1 — locked descriptive holdout (V1, frozen).** Pre-specified,
  commit-locked holdout evaluation of task-selected configurations vs four
  fixed baselines (all direct-answering) on GSM8K/PubMedQA/QASPER, plus the
  exhaustive-landscape search-efficiency audit. Locked before this paper;
  reported here with its confounds made explicit.
- **Tier 2 — fair-baseline dev audit (F1).** Seven presets matched to the
  search-selected configuration's reasoning strategy (six CoT presets plus
  two direct controls), run on the same dev slices the search used
  (GSM8K test[0:100], QASPER items[0:50]) and a pre-chosen 7B shortlist.
  Exploratory: the dev slice influenced selection, and provenance gaps
  apply (§6).
- **Tier 3 — pre-locked cross-benchmark confirmation (F2).** Three
  configurations (the search-selected REF, the strongest CoT preset B2, the
  no-memory CoT control B1) frozen with all 300 SVAMP test IDs, file
  hashes, model revision, and analysis plan *before any inference*;
  evaluated exactly once on the original SVAMP test split; primary and
  secondary contrasts fixed in advance. Independent of the project's
  selection history, but a public benchmark (pretraining contamination
  cannot be ruled out) and not same-distribution with GSM8K.

**Statistics.** All key comparisons are paired at the item level with
paired bootstrap 95% CIs (10,000 resamples, fixed seed). For binary
outcomes (GSM8K, SVAMP, PubMedQA) significance uses two-sided exact McNemar
tests; for continuous QASPER item-level F1 it uses a two-sided exact paired
sign test over non-tied differences. We report CIs and p-values without
treating absence of significance as equivalence.

**Scope.** These are QA-style single-agent cognitive scaffolds above a
frozen LLM. We do not evaluate interactive tool-using, multi-agent,
embodied, or long-horizon environment agents, and our conclusions do not
directly extend to them.

## 4. Tier 1 — Locked Descriptive Holdout: Architecture Matters, Search Credit Unclear

The frozen V1 study (pre-specified, commit-locked before holdout inference)
task-searched configurations on dev slices and evaluated once on untouched
holdouts (GSM8K test[100:1319]; PubMedQA 400 items; QASPER 100 items;
Qwen2.5-1.5B/7B).

**Headline, with its confound.** On GSM8K holdout the search-selected
configuration (recency memory, CoT depth 3, full context) reaches 0.518 at
1.5B and 0.859 at 7B, beating the strongest fixed baseline by +29.0 and
+16.7 percentage points (McNemar p<0.001). However, all four fixed
baselines answered *directly*; the searched configuration used CoT. The gap
is therefore best read as "cognitive architecture choices matter
materially," not as isolated evidence for search or for memory: Tier 2
shows CoT-matched presets close most of it.

**What search-side selection looked like.** Task-conditioned preferences
were stable and interpretable: GSM8K consistently favored CoT-style
reasoning across seeds (3/3, depth 2–3) with the lightweight memory choice
varying among none/recency/retrieval; PubMedQA converged bit-identically to
no-memory direct answering; QASPER shifted the optimum toward retrieval
memory with many exemplars — a pre-specified prediction that was confirmed.
But dev-selected task-specific configurations did not universally
generalize: on PubMedQA and QASPER holdout they were beaten by the
GSM8K-selected configuration.

**Search-efficiency audit (negative).** On the fully enumerated compact
landscape (48 configurations), online evolutionary search does not beat
equal-budget uniform random search at any budget {12, 24, 36, 48} on any
benchmark (20 seeds; differences below 0.01 in AUC and hypervolume). We
make no optimizer-superiority claim.

**Substrate audit (negative).** A real, trainable Mamba-2 memory substrate
participates in the search but is not selected as beneficial under the
protocol. Controlled same-genome ablations found memory effects to be task-
and scale-dependent (neutral at 1.5B on GSM8K, +12.6pp at 7B; +18.0pp at
1.5B on PubMedQA; +1.5pp on QASPER); memory causality is claimed only where
the comparison is controlled.

**Extraction caveat.** A QASPER configuration that works at 1.5B shows
near-zero extracted-answer F1 at 7B; a frozen diagnostic reveals perfect
marker compliance with the answer placed before the marker — a
backbone–prompt–extraction interaction with a substantial extraction
component. It is not evidence of a pure capability collapse, and the
diagnostic does not establish that underlying answer quality is unaffected.

## 5. Tier 2 — Fair CoT-Matched Baselines on Reused Dev (Exploratory)

Tier 1's fairness gap motivated presets matched on the searched
configuration's actual components. We evaluated seven presets plus the
search-selected REF on GSM8K dev (n=100) and QASPER dev (n=50), 1.5B, with
a pre-chosen 7B shortlist (0.16 GPU-hours total).

**GSM8K dev.** Direct presets collapse (B0 none+direct 11.0%; B5
recency+direct 13.0%). Among CoT configurations: B1 (no memory) 50.0%, B4
(reduced context) 49.0%, B3 (retrieval memory) 57.0%, B2 (recency, 3
exemplars) 59.0%, REF (recency, 1 exemplar) 60.0%. Paired: REF−B2 +1.0pp
(p=1.0); REF−B3 +3.0pp (p=0.63); REF−B4 +11.0pp (p=0.043, secondary,
unadjusted); REF−B1 +10.0pp (95% CI [0.0, 20.0], p=0.087, primary
pre-registered contrast). At 7B (dev, secondary, unadjusted): REF−B1 +10.0pp
(p=0.041). The +10pp REF−B1 gap reflects the memory+exemplar component
under CoT, not search; it is directionally consistent with Tier-1's
scale-dependent memory ablation but is exploratory here.

**QASPER dev (exploratory, extraction-sensitive).** REF (0.167) is slightly
*below* B1/B3/B2 (0.184–0.192); paired sign tests are non-significant. Raw
model outputs for these cells were not preserved by the legacy evaluator —
an evidence limitation we carry.

**Provenance limitations.** The F1 run manifest covers only the last four
cells (overwrite-on-invocation defect) and records git_sha as "unknown"
(the VM checkout lacked .git); per-item prediction files for all 15 cells
are committed and were independently re-scored by the Planner, but exact
runner-source provenance is partially undocumented. We report F1 numbers as
accepted-with-limitations, not paper-grade confirmation.

## 6. Tier 3 — Pre-Locked SVAMP Confirmation (Single Shot)

**Protocol.** Before any inference we committed: all 300 original SVAMP
test IDs in order with file SHA-256s (dataset revision pinned), the three
configurations (REF, B2, B1), the backbone (Qwen2.5-1.5B-Instruct, exact
revision), the Body+Question adapter and numeric scorer (versioned,
unit-tested on synthetic fixtures; Equation/Answer never enter prompts),
the primary contrast (REF vs B2) and secondary (REF vs B1), and the
analysis (paired bootstrap CI + exact McNemar). Memory exemplars came from
the GSM8K train calibration bank only; SVAMP train was never read. Zero
normalized exact-match overlap between the 300 locked items and the full
GSM8K corpus was verified pre-inference. A post-hoc read-only forensic
audit re-hashed every committed artifact byte-for-byte (dataset, lock,
900 predictions, paired statistics) and passed, with two honestly annotated
gaps: the run-time loader had checked ordered IDs and count but not full
file bytes (closed post-hoc by the audit), and the on-VM model-revision
observation is not itself a committed artifact.

**Results.** One shot, 0 errors, 0.06 GPU-hours:

| Config | Accuracy (n=300) | Prompt tokens | Completion tokens | Total |
|---|---|---|---|---|
| REF (search-selected: recency k=3, 1 exemplar, CoT d3) | 70.33% (211/300) | 68,017 | 50,049 | 118,066 |
| B2 (strong preset: recency k=3, 3 exemplars, CoT d3) | 71.67% (215/300) | 197,017 | 44,137 | 241,154 |
| B1 (control: no memory, CoT d3) | 70.33% (211/300) | 19,117 | 48,264 | 67,381 |

- **Primary:** REF−B2 = −1.33pp, 95% CI [−6.00, +3.33], exact McNemar
  p=0.67 (23 wins / 27 losses / 250 ties). No detectable advantage of the
  search-selected configuration over the strong preset; B2 is nominally
  +1.33pp with 2.04× REF's total tokens.
- **Secondary:** REF−B1 = 0.00pp, 95% CI [−5.33, +5.33], p=1.0 (34/34/232).
  **B1 matches REF's observed accuracy with 1.75× fewer total tokens**
  (3.56× fewer prompt tokens): in the observed accuracy–token plane REF is
  dominated by B1 — an observation, not a statistically demonstrated
  dominance (CIs include both signs).

**Non-transfer of the dev-side memory benefit.** Tier-2's REF−B1 point
estimate (+10.0pp on GSM8K dev) was *not replicated* on SVAMP (0.00pp). We
state this precisely: the dev estimate did not replicate cross-benchmark.
This is not a formal demonstration of a significant task×memory
interaction (contrasting p-values is not an interaction test), not evidence
of equivalence, and not proof that memory never transfers — it is one
paired, pre-locked non-replication at n=300 resolution (±~5pp).

## 7. What the Evidence Supports

Three claims survive the full audit; three do not.

**Supported.**
1. *Cognitive configuration choices materially affect accuracy and cost.*
   Direct vs CoT reasoning swings GSM8K dev accuracy 11–13% → 49–60%; the
   locked holdout gap of the searched CoT configuration over direct fixed
   baselines is +29.0/+16.7pp; token cost varies ~10× among CoT presets
   with similar accuracy (and 3.6× prompt-token spread on SVAMP).
2. *Task-conditioned selection is stable and interpretable at the family
   level.* CoT-dominant configurations win on GSM8K across seeds; PubMedQA
   converges to no-memory direct; QASPER shifts toward retrieval memory
   (pre-specified, confirmed).
3. *Search-side preferences can fail to generalize.* Dev-selected
   task-specific configurations lost to the GSM8K configuration on two
   holdouts (Tier 1); the dev-side memory benefit did not replicate on
   SVAMP (Tier 3). Held-out, fair-baseline, cross-benchmark auditing is
   what separates specialization from generalizable advantage.

**Unsupported (and we claim them nowhere).**
1. *Search superiority.* No detectable REF advantage over strong presets in
   Tiers 2–3; evolutionary search ≈ equal-budget random search on the
   enumerated landscape (Tier 1).
2. *Universal or scale-growing memory benefit.* Effects are task- and
   scale-dependent; the one pre-locked cross-benchmark test found none.
3. *Neural substrate benefit.* The trainable Mamba-2 substrate is
   implemented and searchable but not selected as beneficial.

## 8. Limitations

Single model family (Qwen2.5, 1.5B/7B); SVAMP is a public benchmark —
pretraining contamination cannot be ruled out, and it is not
same-distribution with GSM8K, so Tier 3 is cross-benchmark rather than
i.i.d. confirmation. Dev slices are small (n=100/50) and were exposed to
selection (Tier 2 is exploratory; 7B and B4 contrasts are secondary and
unadjusted for multiplicity). n=300 gives ±~5pp CI resolution; absence of
detectable differences is not equivalence. Tier-1 fixed baselines were
direct-only, so its headline cannot be attributed to search alone. F1
provenance is partially undocumented (manifest coverage, runner git_sha)
and QASPER dev raw outputs were not preserved. QASPER scoring is
extraction-sensitive (marker placement), which we diagnose but do not claim
to fix. Our scaffolds are QA-style single-agent configurations; nothing
here directly addresses interactive tool-use, multi-agent, embodied, or
long-horizon agents, or backbones outside one family.

## 9. Reproducibility and Ethics

All evaluation code, locked protocols, configuration files, per-item
predictions (900/900 with full raw completions for Tier 3), statistics
scripts, the read-only forensic verifier, and figure scripts are included
in the anonymous supplementary. Tier-1/V1 artifacts are frozen at their
locked commits; Tier-3 was pre-locked before inference and is auditable
byte-for-byte. Experiments used <0.25 GPU-hours for Tiers 2–3 combined. The
work uses public benchmarks (GSM8K, SVAMP, PubMedQA, QASPER/LongBench) and
public models, involves no human subjects, and reports negative results and
failure modes explicitly. We release no new model weights and see no
foreseeable misuse beyond that of the underlying public LLMs.

## References

(see references.bib)

- Yao et al., ReAct: Synergizing Reasoning and Acting in Language Models, ICLR 2023.
- Shinn et al., Reflexion: Language Agents with Verbal Reinforcement Learning, NeurIPS 2023.
- Wei et al., Chain-of-Thought Prompting Elicits Reasoning in Large Language Models, NeurIPS 2022.
- Hu et al., ADAS: Automated Design of Agentic Systems, ICLR 2025.
- Shang et al., AgentSquare: Automatic LLM Agent Search in Modular Design Space, ICML 2025.
- Zhang et al., MaAS: Multi-agent Architecture Search via Agentic Supernet, ICML 2025.
- Evo-Memory: Benchmarking LLM Agent Test-time Learning with Self-Evolving Memory, 2025.
- Khattab et al., DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines, 2023/2024.
- Guo et al., EvoPrompt: Connecting LLMs with Evolutionary Algorithms, 2023/2024.
- Real et al., Regularized Evolution for Image Classifier Architecture Search, AAAI 2019.
- Deb et al., NSGA-II, IEEE TEVC 2002.
- Novikov et al., AlphaEvolve, 2025.
- Gu & Dao, Mamba: Linear-Time Sequence Modeling with Selective State Spaces, 2023/2024.
- Dao & Gu, Mamba-2: Transformers are SSMs, ICML 2024.
- Cobbe et al., GSM8K: Training Verifiers to Solve Math Word Problems, 2021.
- Patel et al., SVAMP: Are NLP Models really able to Solve Simple Math Word Problems?, NAACL 2021.
- Jin et al., PubMedQA, EMNLP 2019.
- Dasigi et al., QASPER, 2021; Bai et al., LongBench, ACL 2024.
- Qwen Team, Qwen2.5, 2024/2025.
- Lewis et al., Retrieval-Augmented Generation, NeurIPS 2020.
- Snoek et al., Practical Bayesian Optimization, NeurIPS 2012.
