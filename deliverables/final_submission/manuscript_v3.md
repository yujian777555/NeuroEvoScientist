# NeuroEvoScientist: Task-Conditioned Cognitive Architecture Co-Design for LLM Agents

## A Controlled Study of Generalization, Cost, and Failure Modes

---

## Abstract

LLM agents are usually deployed with a fixed, manually designed cognitive
architecture. We ask whether per-task co-design of an agent's reasoning
strategy, episodic memory/exemplar policy, and context allocation — above a
frozen backbone — materially changes capability–cost behavior, and whether
task-conditioned search generalizes.

We present NeuroEvoScientist, a controlled study over a structured,
hierarchical family of agent configurations, with leakage-safe calibration
splits, raw multi-objective logging, task-aware phenotype canonicalization,
pre-specified and commit-locked holdout evaluation, and paired item-level statistics across
two frozen backbones (Qwen2.5-1.5B / 7B).

Four findings stand out. First, cognitive architecture choices change
capability–cost behavior materially: on untouched GSM8K holdout, a searched
configuration outperforms the strongest fixed baseline by +29.0 percentage
points at 1.5B and +16.7 points at 7B (McNemar p<0.001), while a controlled
same-genome GSM8K ablation shows the memory effect increasing from
approximately zero at 1.5B to +12.6 points at 7B. Second, search-side architecture
preferences differ clearly and stably by task — a long-context scientific-QA
task shifts the optimum to retrieval-based memory, as pre-specified — yet
dev-selected task-specific architectures do not universally generalize: on
PubMedQA and QASPER holdout they are beaten by the configuration selected
for GSM8K. Third, task–backbone interactions are substantial: a QASPER
configuration that works at 1.5B collapses at 7B, and our diagnostic shows
this reveals a substantial answer-format/extraction component, so the near-zero extracted-answer F1 should not be interpreted as evidence of a pure capability collapse.
Fourth, equal-budget evolutionary search does not beat random search in this
compact space, and a real trainable Mamba-2 substrate is not selected as
beneficial — we keep both as audit findings rather than hiding them.

The work contributes a leakage-safe, falsifiable protocol for agent
architecture co-design and a careful map of where task-conditioned
specialization does — and does not — generalize.

---

## 1. Introduction

LLM agents are typically assembled by hand: a reasoning pattern, a memory
mechanism, and a context budget are chosen once and reused across tasks. Yet
different tasks place different demands on each of these components —
multi-step arithmetic rewards explicit reasoning steps, biomedical judgment
rewards calibrated abstention, and long-document question answering rewards
context allocation and evidence retrieval. This paper asks two questions.
First, do these cognitive architecture choices materially change an agent's
capability–cost behavior when the underlying language model is kept frozen?
Second, can automatic, task-conditioned search over such choices find
configurations that remain superior on data untouched by the search itself?

We answer both questions with NeuroEvoScientist, a controlled co-design
framework in which an agent configuration is a structured genome over
reasoning strategy, episodic memory policy, and context policy, evolved with
multi-objective selection and evaluated under a leakage-safe, pre-specified,
commit-locked protocol. Our study deliberately audits its own search procedure: we
enumerate the compact search space exhaustively to obtain a ground-truth
landscape, we compare evolutionary search to equal-budget random search at
budgets below full coverage, and we hold out benchmark items that the search
never sees.

Our findings are deliberately two-sided. On the positive side, architecture
choices matter enormously: the searched GSM8K configuration beats the strongest fixed
baseline by +29.0 percentage points at 1.5B and +16.7 points at 7B, while task-specific gene
distributions are stable across seeds, and a pre-specified prediction — that
a long-context task shifts the optimum toward retrieval memory — is
confirmed. On the negative side, dev-selected task-specific architectures do
not universally generalize; equal-budget random search matches evolutionary
search in our compact space; and a real Mamba-2 substrate, though correctly
implemented and trainable, is not selected as beneficial. We report these
negative results as part of the contribution.

## 2. Related Work

LLM agents commonly chain reasoning and acting through manually designed
scaffolds such as ReAct and Toolformer, or through self-reflection loops
such as Reflexion; DSPy compiles declarative LLM calls into optimizable
pipelines. Most closely related to us are automated agent-design frameworks:
ADAS searches over agent programs expressed in code, and AgentSquare
searches a modular design space of planning, reasoning, tool-use, and memory
modules. Both optimize for performance alone. We differ by (i) searching
per-task cognitive configurations with real memory substrates rather than
workflow topology, (ii) evaluating under multiple raw objectives instead of
a single score, and (iii) pre-specified, commit-locked held-out auditing with paired
statistics, reporting where specialization does and does not generalize.

Prompt-level strategy choices — chain-of-thought, verification, planning —
materially affect accuracy, and EvoPrompt evolves prompt text. We treat the
reasoning strategy as one gene jointly searched with memory and context
policy. Retrieval-augmented generation grounds LLMs in external evidence;
our memory policies manage a calibration-only experience bank and we
quantify when episodic memory helps, hurts, or is neutral.

Our search draws on evolutionary computation and NAS: regularized evolution
is a strong NAS baseline, and multi-objective selection follows an NSGA-II-style non-dominated-sorting and crowding-distance procedure;
Bayesian optimization is the standard sample-efficiency reference. Unlike
NAS over backbone weights, our search operates above a frozen LLM, and we
audit the search procedure against equal-budget random search on a fully
enumerated landscape. We share AlphaEvolve's evolutionary loop but change
the object of evolution to agent cognitive configurations. Mamba and Mamba-2
provide the selective state-space models from which our real trainable
memory substrate is built. We evaluate on GSM8K, PubMedQA, and QASPER in its
LongBench form — three tasks with genuinely different cognitive demands —
using frozen Qwen2.5-Instruct backbones. We claim no priority over any of
these works; our contribution is a controlled, leakage-safe, multi-objective
audit of task-conditioned co-design, including its failure modes.

## 3. Problem Formulation

An agent configuration is a genome over three gene families: memory policy,
reasoning strategy, and context policy. Given a task and a frozen backbone,
we seek configurations that occupy favorable positions on the
capability–cost Pareto frontier — not a single scalar optimum. Task
conditioning means the preferred configuration may differ per task; the
scientific question is whether search-side preferences correspond to
generalizable holdout advantages or merely to search-split overfitting.

## 4. Method

Our method has two layers (full details in Section 5).

**Compact audit layer.** A flat genome over memory (recency, retrieval,
mamba2, hybrid), reasoning (direct, chain-of-thought, verify, planner), and
context policy (full, truncated, answer-only) defines 48 configurations. We
evaluate all of them per benchmark to obtain an exhaustive landscape with
raw objectives — capability, efficiency, prompt-token cost, latency, and
adaptation cost — used as an analysis oracle for the search-efficiency audit.

**Structured co-design layer.** The final search space refines each gene
with conditional sub-genes: memory recall width and similarity metric,
Mamba-2 state size, hybrid mixing fraction, reasoning depth and verifier
passes, exemplar word budget and count, input-context word budget for
long-document tasks, and a per-candidate substrate-adaptation budget.
Normalization removes semantically inactive sub-genes before hashing, so
duplicate phenotypes are never double-counted; a task-aware canonicalization
additionally drops the input-context budget outside long-context tasks.
Mutations are local (neighboring values for ordered sub-genes), crossover
swaps semantic blocks and normalizes, and selection is non-dominated sorting
with crowding-distance diversity over raw objectives; scalar fitness is used
only for logging.

All memory banks are built exclusively from calibration splits; test items
never enter the bank. Candidates carrying the trainable Mamba-2 substrate
receive a fixed adaptation budget with the backbone frozen; substrate weights
can be inherited from parents as an appendix mechanism evaluated separately.

## 5. Experimental Setup

**Benchmarks and splits.** GSM8K uses test[0:100] for search/dev and
test[100:1319] (1,219 items) for holdout; the memory bank uses only the
train split. PubMedQA uses samples[0:100] for dev, samples[100:500] (400
items) for holdout, and samples[500:1000] for calibration. QASPER (200 items)
uses items[0:50] for dev, items[50:150] for holdout, and items[150:200] for
calibration. Pairwise disjointness is enforced by unit tests. Selection
locks were committed before any holdout inference.

**Backbones.** Qwen2.5-1.5B-Instruct for search and selection;
Qwen2.5-7B-Instruct for transfer only (no re-search). Greedy decoding,
256 max new tokens, batch 32, FP16. Exact model revisions and dataset
acquisition details are in the reproducibility appendix.

**Search-efficiency audit.** On the compact landscape, online ENSS and
uniform random search are compared at evaluation budgets {12, 24, 36, 48}
across 20 search seeds, measuring best capability, Pareto hypervolume,
regret to the global front, epsilon-Pareto hit probability,
evaluations-to-threshold, and area under the best-so-far curve.

**Statistics.** All key comparisons are paired at the item level. Paired
bootstrap 95% confidence intervals (10,000 resamples, fixed seed) are
reported for all tasks. For binary GSM8K and PubMedQA outcomes, significance
uses exact McNemar tests. For continuous QASPER item-level F1, significance
uses a two-sided exact paired sign test over non-tied differences.

## 6. Main Results

**R1 — Architecture choices matter materially.** On untouched GSM8K
holdout, the searched configuration A_gsm (recency memory, chain-of-thought
depth 3, full context) achieves 0.518 at 1.5B and 0.859 at 7B, beating the
strongest fixed baseline by +29.0 and +16.7 percentage points respectively
(McNemar p<0.001; Table A). On PubMedQA, searched configurations produce
competitive capability–cost tradeoffs but not universal capability
superiority; a fixed retrieval baseline remains slightly ahead at 1.5B, so
we report the asymmetry rather than hiding it (Table A).

**R2 — Task-conditioned selection is stable and interpretable.** Across
three search seeds, GSM8K consistently favors CoT-style reasoning (3/3 seeds, depth 2–3), while the lightweight memory choice varies across none, recency, and retrieval, PubMedQA converges bit-identically to no-memory direct answering on
all three seeds, and QASPER converges to retrieval-based memory with many
exemplars and a reduced document budget — matching our pre-specified
prediction that a long-context task shifts the optimum toward retrieval
(Figure 2). A sensitivity audit after task-aware phenotype canonicalization
leaves these families unchanged (PubMedQA is bit-identical; GSM8K varies
only within the same family).

**R3 — Dev-selected preferences do not universally generalize.** On GSM8K
holdout, the own-task configuration dominates every alternative by +31 to
+71 points (p<0.001). On PubMedQA and QASPER holdout, however, the
task-selected configurations are beaten — significantly — by the
GSM8K-selected configuration (Table B). Search-side specialization is real,
but dev-slice preferences can overfit.

**R4 — Memory effects are task- and scale-dependent.** Under
same-genome ablation, removing episodic memory is neutral at 1.5B on GSM8K
but removes 12.6 points at 7B (p<0.001); on PubMedQA, enabling memory on the
frozen configuration adds +18.0 points at 1.5B; on QASPER the effect is
small (+1.5 points; Table C). Memory causality is claimed only where the
comparison is controlled.

**R5 — Task–backbone interaction diagnosed as format/extraction, not
capability.** Several QASPER configurations appear to collapse at 7B
(near-zero extracted-answer F1). Our frozen diagnostic shows marker
compliance is perfect (100%) while extracted-answer F1 is zero and
whole-continuation F1 remains positive — the 7B backbone places its answer
before or at the marker instead of after it. This is a
backbone–prompt/extraction interaction with a substantial extraction component; the diagnostic does not establish that underlying answer quality is unaffected
(Figure 4).

## 7. Generalization Audit and Failure Analysis

The compact-space audit finds no search-efficiency advantage for
evolutionary search over equal-budget random search at any budget or
benchmark (differences below 0.01 in AUC and hypervolume across 20 seeds;
Figure 6). We therefore make no optimizer-superiority claim; evolution is
the architecture-generation mechanism, and our contribution is the
task-conditioned co-design evidence and the audit protocol itself. A real,
trainable Mamba-2 substrate participates in the search but is not selected
as beneficial under our protocol; we keep this negative result. Weight
inheritance improves post-adaptation loss in all 20 paired cases but yields
no capability difference in any of them; it is reported as an appendix
mechanism.

## 8. Mechanism Analysis

Fourteen auditable case studies link genome choices to inference behavior:
successful and failed GSM8K items with recalled exemplars, PubMedQA
decisions, and paired QASPER 1.5B/7B failures with raw outputs and extracted
answers. These cases illustrate how exemplar content, context budget, and
answer-formatting instructions jointly shape outcomes (Section 9 artifacts).

## 9. Limitations

Our study uses a single model family (Qwen2.5 at 1.5B and 7B), a compact
audited space, prompt-level reasoning genes, and a single adaptation
protocol. PubMedQA's three-way ceiling limits capability separation, and
QASPER's answer extraction is marker-sensitive, which we diagnose rather
than hide. Cross-backbone latency is not compared without normalization.
Evolutionary superiority is not supported in our space; we do not claim it.
Small dev slices can overfit, as our own PubMedQA/QASPER results show.

## 10. Conclusion

Cognitive architecture choices materially change agent capability–cost
behavior. Automatic co-design exposes clear, stable, interpretable
task-conditioned preferences — and a rigorous held-out audit is what
distinguishes search-side specialization from generalizable advantage. We
release the full protocol, landscapes, per-item predictions, statistics, and
claim audit to make this kind of study falsifiable by construction.

## 11. Reproducibility and Ethics Statement

All experiments are frozen at the locked commits; exact model revisions,
dataset acquisition details, protocol parameters, cache semantics, and the
result-to-evidence map are documented in the reproducibility appendix. The
work uses public benchmarks and public models, involves no human subjects,
and reports negative results and failure modes explicitly.

---

### Tables and Figures

- **Table A** (Main results): `paper/phase21_tables.md`, Table A.
- **Table B** (Transfer and ablations): `paper/phase21_tables.md`, Tables B–C.
- **Figure 2** (Task gene distributions): `paper/figures/fig2_gene_distributions.png`.
- **Figure 3** (Holdout transfer matrices): `paper/figures/fig3_transfer_matrix_{15b,7b}.png`.
- **Figure 4** (QASPER diagnosis): `paper/figures/fig4_qasper_diag.png`.
- **Figure 5** (Controlled memory ablation): `paper/figures/fig5_memory_ablation.png`.
- **Figure 6** (Compact-space landscape): `paper/figures/fig6_landscape_pareto.png`.
