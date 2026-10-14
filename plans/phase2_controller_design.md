# Phase-2 Method Design — Task-Adaptive Cognitive Configuration Controller (TACC)

Date: 2026-10-14
Status: DESIGN ONLY (no code, no experiments). Awaiting Planner review.
Grounding: frozen Phase-1 evidence (V1 locked study, F1 fair-baseline dev
audit, F2 pre-locked SVAMP confirmation). No number in this document is new;
all are citations of locked artifacts.

---

## 0. Positioning

Phase-1 answered: *"Can search find the best agent configuration?"* —
answer: search finds configurations whose headline gains are largely
attributable to reasoning scaffolds and baseline imbalance, not to the
optimizer; and dev-selected optima are task-specific.

Phase-2 asks the upgraded question:

> **Can an agent automatically adapt its cognitive configuration to task
> characteristics — instead of searching for one global best configuration?**

The proposed system is the **Task-Adaptive Cognitive Configuration
Controller (TACC)**: a learned mapping `task -> cognitive configuration`
over the *same* audited configuration space as Phase-1.

---

## 1. Why a controller? The static-search failure evidence

Phase-1 provides direct, locked evidence that a single static configuration
is structurally inadequate:

| Evidence | Locked source | Implication |
|---|---|---|
| Task-selected optima differ by task family: GSM8K → recency+CoT (depth 2–3); PubMedQA → none+direct (bit-identical across 3 seeds); QASPER → retrieval+many exemplars | V1 frozen selection locks | No universal configuration exists even within one backbone |
| Dev-selected task configs lose to the GSM8K config on other tasks' holdouts (PubMedQA, QASPER) | V1 holdout matrices (Tier 1, R3) | Static per-task selection overfits its dev slice |
| F1 dev: REF−B1 = +10.0pp (exploratory); F2 SVAMP: REF−B1 = 0.00pp (p=1.0) | F1/F2 locked results | A memory configuration with dev benefit does not transfer across benchmarks |
| F2 cost: B1 matches REF accuracy (70.33%) with 1.75× fewer total tokens | F2 manifest | "Best" is multi-objective; accuracy-only selection is misleading |
| Equal-budget evolution ≈ random search on the enumerated 48-config landscape | Phase-18 audit | Better *search* is not the bottleneck; better *conditioning* might be |

Static failure mode, stated precisely:

```
Task A ──search──> Best Config A      (e.g. GSM8K: recency + CoT d3)
Task B ──search──> Best Config B      (e.g. PubMedQA: none + direct)
                     ∧
                     └── no single config is best everywhere,
                         and dev-side argmax can fail out-of-distribution
```

A controller replaces the *static argmax* with a *conditional policy*:
the configuration becomes a function of measurable task properties rather
than a constant per benchmark or per deployment.

### 1.1 What TACC is NOT (scope guards inherited from Phase-1)

- Not backbone weight training / not NAS over the LLM.
- Not online memory evolution (Evo-Memory style); the memory bank remains
  calibration-only and frozen at evaluation time.
- Not interactive tool-use / multi-agent routing; still QA-style
  single-agent scaffolds.
- Not a claim that conditioning will beat strong fixed configs — that is
  the empirical question, with negative outcomes reportable.

---

## 2. Controller architecture

```
                 Task Input (question text + task metadata)
                        |
                        v
                Task Encoder
   (embedding + hand features: length, difficulty proxy,
    reasoning-pattern cues, domain tag)
                        |
                        v
             Cognitive Controller (policy)
                        |
      +-----------------+------------------+
      |                 |                  |
  reasoning strategy  memory policy     context policy
  (direct/cot/verify, (none/recency/    (full/truncated/
   depth)              retrieval, k,     answer-only,
                       exemplar count)   word budget)
      |                 |                  |
      +-----------------+------------------+
                        |
                        v
              LLM Execution (frozen backbone,
                           fixed decoding)
                        |
                        v
                 Answer + token meter
```

### 2.1 Inputs (task features)

All features must be computable **before** any task LLM inference and must
be logged per item:

- **Question embedding**: small frozen encoder (e.g. a MiniLM-class
  sentence encoder) — cheap, CPU-feasible.
- **Surface features**: character/token length, numeric-token density,
  question type markers.
- **Difficulty proxy**: e.g. reference-solution step count on train (never
  test), or a calibrated heuristic; must be computed without test labels.
- **Reasoning-pattern cue**: few-shot probe is explicitly *not* allowed at
  selection time if it consumes the task's answer budget — keep the
  controller input inference-free w.r.t. the target LLM. (Optional probe
  variant is a separate ablation with its own cost accounting.)
- **Domain tag**: dataset identity where legitimately available; a
  domain-tag-only controller is the trivial baseline to beat.

### 2.2 Outputs (configuration policy)

Discrete selection over the audited Phase-1 configuration space — not
continuous generation of new configs:

- `reasoning`: {direct, cot(d∈{2,3}), verify}
- `memory`: {none, recency(k), retrieval(metric,k), exemplar_count}
- `context`: {full, truncated, answer_only, word_budget}

**Design decision — discrete policy, not continuous synthesis.**
Rationale: (i) every selectable configuration is already validated and
cache-compatible with Phase-1 evaluators; (ii) discrete policies are
auditable (each choice maps to a locked config hash); (iii) continuous
config generation would create unaudited pipelines, violating the project's
falsifiability standard.

### 2.3 Constraint: controller overhead is metered

Controller inference (embedding + policy head) consumes compute and adds
latency. Its cost is reported alongside task LLM tokens, and a controller
that saves LLM tokens but costs more overall is a negative result, not a
detail to hide.

---

## 3. Learning approaches — comparison

| | A. Supervised (utility-labeled) | B. Reinforcement learning | C. Contextual bandit |
|---|---|---|---|
| Signal | per-task best config label from calibration evaluation | reward = score − λ·cost per episode | per-task arm pull: config → reward |
| Data need | full config × train-task matrix (expensive once, reusable) | many online rollouts; high | online or logged bandit data; moderate |
| Implementation | low (classifier/regressor over configs) | high (unstable, reward hacking risk) | medium (LinUCB/Thompson or neural CB) |
| Novelty for paper | moderate (clean, interpretable) | high (but high risk) | moderate–high |
| Main risk | argmax labels from small dev slices are noisy (Phase-1 showed ±5pp CI at n=300) | cost blowup; irreproducibility | exploration cost; cold start |
| Audit fit | excellent (labels traceable to locked caches) | poor | good |

**Recommendation: Approach A first (supervised, utility-labeled), C as the
online extension, B explicitly deferred.**

Concretely:

1. Build the label matrix on **GSM8K train calibration only**: evaluate the
   candidate config set on N train items (never test), giving per-item
   accuracy + tokens per config.
2. Define per-item utility `u(item, cfg) = correct − λ · normalized_tokens`,
   with λ pre-specified (e.g. chosen so that 1pp accuracy ≈ a fixed token
   budget; λ locked before training).
3. Train a cost-sensitive classifier/ranker: features → distribution over
   configs (or per-config utility regression + argmax).
4. TACC output at test time: single configuration per item (hard routing).
   Soft mixtures are out of scope (they mix pipeline outputs, breaking
   per-config auditability).
5. Contextual bandit (C) is the designated follow-up: it reuses the same
   reward definition and allows the controller to adapt to a new
   distribution with a small number of labeled items — a natural match to
   the "adaptation" story. RL (B) is deferred: its compute and stability
   profile is incompatible with the project's <1 GPU-hour audit culture.

### 3.1 The central scientific risk (preview of risk doc)

Phase-1 config effects were measured at the **task level** (GSM8K vs
PubMedQA vs QASPER), not the **instance level**. If, within one benchmark,
the per-item best configuration barely varies (e.g. CoT-always wins within
GSM8K), then TACC has nothing to learn beyond the fixed choice, and the
honest result is "instance-level adaptation is not needed within-task;
task-level conditioning is where the variance lives." The experiment design
(document 2) therefore starts with a **variance-measurement gate**.

---

## 4. Evaluation contract (inherited, non-negotiable)

- Pre-locked configuration set, pre-locked test IDs, pre-specified primary
  contrasts, byte-hashed artifacts, paired item-level statistics
  (exact McNemar / paired sign test / bootstrap CIs, fixed seeds).
- No test-set peeking for controller design decisions.
- Negative results are reportable outcomes.
- Single backbone family first (Qwen2.5-1.5B), exactly as F2.

---

## 5. Open questions for the Planner

1. Approve discrete-policy scope (vs continuous config synthesis)?
2. Approve utility λ definition and its pre-specification procedure?
3. Approve "supervised first, bandit second, RL deferred" sequencing?
4. Is a domain-tag-only controller acceptable as the trivial baseline to
   beat, or should it be excluded as leakage-adjacent?
