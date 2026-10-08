# Related Work (final, citation-backed)

## Agent architectures and workflow optimization

LLM agents commonly chain reasoning and acting through manually designed
scaffolds (Yao et al., 2023, ReAct; Schick et al., 2023, Toolformer) and
self-reflection loops (Shinn et al., 2023, Reflexion). DSPy compiles
declarative LLM calls into optimizable pipelines (Khattab et al., 2023).
These frameworks optimize prompts or workflow structure; our work instead
co-designs an agent's cognitive configuration — reasoning strategy, episodic
memory policy, and context allocation — under explicit capability–cost
objectives with a frozen backbone.

## Automated agent search

Most closely related are automated agent-design frameworks: ADAS (Hu et al.,
2024) searches over agent programs expressed in code, and AgentSquare (Shang
et al., 2025, ICLR) searches a modular design space of planning, reasoning,
tool-use, and memory modules. MaAS performs query-dependent multi-agent
architecture search through an agentic supernet and explicitly considers
inference resources (Zhang et al., 2025, ICML). In contrast, our search target
is the internal cognitive configuration of a single frozen-backbone agent —
reasoning policy, episodic memory, and context allocation — and our main
emphasis is the gap between search-side specialization and held-out
generalization under a commit-locked protocol. These frameworks optimize for
performance alone. We differ
in three respects: (i) our search object is a per-task cognitive
configuration with real memory substrates rather than workflow topology;
(ii) we evaluate under multiple raw objectives (capability, prompt-token
cost, latency, adaptation cost) rather than a single score; and (iii) we run
a pre-specified, commit-locked held-out audit with paired statistics, reporting where
task-conditioned specialization does and does not generalize.

## Prompt and reasoning strategy optimization

Prompt-level strategy choices — chain-of-thought (Wei et al., 2022),
verification, planning — materially affect downstream accuracy. EvoPrompt
(Guo et al., 2023) evolves prompt text. We treat the reasoning strategy as
one gene among several, jointly searched with memory and context policy.

## Episodic and retrieval memory for agents

Retrieval-augmented generation grounds LLMs in external evidence (Lewis et
al., 2020). Recent work studies continually evolving or self-updating agent memory (e.g., Evo-Memory, Wei et al., 2025). Our setting differs: memory is not evolved online during deployment; instead, memory policy is one component of a task-conditioned cognitive configuration searched using a fixed calibration-only experience bank.

Our memory policies (recency, retrieval via term-frequency cosine or hashed bag-of-words cosine — neither uses IDF — and a trainable
Mamba-2 substrate) manage an experience bank built strictly from calibration
splits, and we quantify when episodic memory helps, hurts, or is neutral
across tasks and backbones.

## Evolutionary computation and NAS

Neural architecture search is surveyed by Elsken et al. (2019); regularized
evolution is a strong NAS baseline (Real et al., 2019). Multi-objective selection follows an NSGA-II-style non-dominated-sorting and crowding-distance procedure (Deb et al., 2002).
Bayesian optimization is the standard sample-efficiency reference (Shahriari
et al., 2016). In contrast to NAS over backbone weights, our search operates
above a frozen LLM, and our audit compares evolutionary search to
equal-budget random search on a fully enumerated landscape rather than
assuming evolutionary superiority.

## Automated discovery and AlphaEvolve

AlphaEvolve (Google DeepMind, 2025) evolves programs through LLM proposals
and evaluators. We share the evolutionary loop but change the object of
evolution to agent cognitive configurations, and we explicitly audit the
search procedure itself.

## Memory and state-space models

Mamba (Gu & Dao, 2023) and Mamba-2 (Dao & Gu, 2024) provide efficient
selective state-space sequence models. We include a real, trainable Mamba-2
memory substrate in our search space; under our protocol it is valid but not
selected as beneficial — we report this as a finding, not a failure to tune.

## Benchmarks

We evaluate on GSM8K (Cobbe et al., 2021), PubMedQA (Jin et al., 2019), and
QASPER in its LongBench form (Dasigi et al., 2021; Bai et al., 2023), chosen
for genuinely different cognitive demand profiles (multi-step arithmetic,
biomedical judgment, long-context evidence integration). All backbones are
Qwen2.5-Instruct (Yang et al., 2024).

## Positioning statement

We do not claim priority over any of the above. Our contribution is a
controlled, leakage-safe, multi-objective audit of task-conditioned
cognitive architecture co-design, including its failure modes.
