# Method (final, Phase-21)

> The paper's method operates in two layers. The compact audit layer
> establishes the landscape reference and the search-efficiency audit; the
> structured co-design layer is the final search space used for
> task-conditioned selection and holdout evaluation.

## 1. Overview

We study whether an LLM agent's cognitive architecture can be automatically
co-designed per task above a frozen backbone. A configuration is treated as
an evolutionary object:

```
Task -> Genome (normalized, task-aware) -> Evolution Controller
     -> Agent Population -> Multi-objective Evaluation -> Pareto Selection
     -> Next Generation
```

## 2. Layer 1 — Compact audit space (48 phenotypes)

A flat genome over three genes, used for the exhaustive landscape and the
search-efficiency audit:

```
memory:   recency | retrieval | mamba2 | hybrid
reasoning: direct | cot | verify | planner
context_policy: full | truncated | answer_only
quantization: fp16 (fixed; not searched)
```

- **Memory**: an episodic experience bank built only from the benchmark's
  train/calibration split (leakage-free). `recency` returns the most recent
  k entries; `retrieval` returns top-k by term-frequency cosine over sparse lexical vectors (no inverse-document-frequency weighting, so we do not call it TF-IDF); `mamba2` runs a real,
  trainable Mamba-2 substrate (Transformers `Mamba2Model`) over the bank as
  an ordered sequence and scores candidates against the resulting
  order-dependent memory state; `hybrid` mixes retrieval with the most
  recent entry.
- **Reasoning**: distinct instruction templates (direct / chain-of-thought /
  verify / planner).
- **Context policy**: exemplar verbosity (full / truncated / answer_only),
  which changes real prompt-token cost.

Every gene changes real inference behavior; this is enforced by unit tests.

## 3. Layer 2 — Structured co-design space (hierarchical, conditional)

The final search space refines each gene with sub-genes that are active only
where semantically valid:

```
memory.type: recency | retrieval | mamba2 | hybrid
memory.k: 1..8                       (exemplar cap)
memory.retrieval_metric: tf_cosine | hashed_bow (sparse lexical / hashed bag-of-words; no IDF)
memory.state_size: 32..256                   (mamba2 only)
memory.hybrid_fraction: 0.25..0.75           (hybrid only)
reasoning.strategy: direct | cot | verify | planner
reasoning.depth: 1..4                        (cot/planner only)
reasoning.verifier_passes: 1..3              (verify only)
context.mode: full | truncated | answer_only
context.exemplar_word_budget: 128..1024      (truncated/answer_only only)
context.exemplar_count: 0..8                 (0 = canonical no-memory)
input_context.budget: 512..4096 words        (long-document tasks only)
adaptation.enabled: bool
adaptation.steps: 0..40                      (enabled + mamba2 only)
```

Normalization removes inactive sub-genes before hashing/evaluation, so
duplicate phenotypes are never counted as distinct architectures. A
task-aware phenotype additionally drops `input_context.budget` outside
long-context tasks.

## 4. Operators

- **Mutation**: local moves to neighboring values for ordered sub-genes
  (80% of mutations), categorical re-sampling for type-level genes; type
  changes re-activate dependent sub-genes consistently.
- **Crossover**: semantic block swap (memory / reasoning / context /
  adaptation) followed by normalization.
- **Selection**: NSGA-style non-dominated sorting with crowding-distance
  diversity over raw objectives. Scalar fitness is for logging only.
- **Weight inheritance** (appendix mechanism): children sharing a parent's
  substrate inherit its post-adaptation weights.

## 5. Candidate adaptation

For genomes with a trainable substrate (`memory.type=mamba2`), the substrate
is adapted on the calibration split with a fixed budget (48 samples, 30
AdamW steps, fixed learning rate and seed). The backbone is never trained.

## 6. Relationship to prior paradigms

AlphaEvolve evolves programs; NAS evolves static networks; agent-workflow
search optimizes cooperation topology. Here the search object is a single
agent's cognitive configuration under multi-objective capability–cost
criteria, with an explicit audit of the search procedure itself.
