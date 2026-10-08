# Abstract v2（Phase-21 终版；只用可辩护 claim）

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
points at 1.5B and +16.7 points at 7B (McNemar p<0.001), while a same-genome memory ablation
shows the controlled GSM8K memory effect increasing from approximately zero at 1.5B to +12.6 points at 7B. Second, search-side architecture preferences differ
clearly and stably by task — a long-context scientific-QA task shifts the
optimum to retrieval-based memory, as pre-specified — yet dev-selected
task-specific architectures do not universally generalize: on PubMedQA and
QASPER holdout they are beaten by the configuration selected for GSM8K.
Third, task–backbone interactions are substantial: a QASPER configuration
that works at 1.5B collapses at 7B, and our diagnostic shows this is an
answer-format/extraction interaction with a substantial extraction component, rather than evidence of a pure capability collapse. Fourth,
equal-budget evolutionary search does not beat random search in this compact
space, and a real trainable Mamba-2 substrate is not selected as beneficial —
we keep both as audit findings rather than hiding them.

The work contributes a leakage-safe, falsifiable protocol for agent
architecture co-design and a careful map of where task-conditioned
specialization does — and does not — generalize.
