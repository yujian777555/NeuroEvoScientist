# Phase-15 Plan: Neural Substrate Activation

## Objective

Phase-14 successfully completed the first real GSM8K evolution experiment. However, analysis revealed that current capability gains mainly come from reasoning prompt templates, while memory/compression genes are not yet connected to real inference.

Phase-15 goal:

Transform ENSS from prompt-level configuration evolution into real neural substrate evolution.

---

# Research Question

Can evolution discover better combinations of real agent cognitive substrates?

The claim should move from:

"Evolution selects better prompts"

into:

"Evolution discovers adaptive memory-reasoning-efficiency configurations for LLM agents."

---

# Task 1: Real Memory Substrate Integration

Implement actual memory modules:

- Mamba Memory Adapter
- Retrieval Memory Adapter
- Hybrid Memory Adapter

Architecture:

Qwen Backbone

+

Memory Substrate

+

Reasoning Module

+

Tool Interface

Genome should control the real computation graph.

---

# Task 2: Genome Activation

Current genome:

memory
reasoning
compression

Upgrade requirement:

Each gene must affect inference behavior.

Example:

memory=mamba

must instantiate Mamba memory module.

memory=retrieval

must instantiate retrieval module.

---

# Task 3: Add Scientific Benchmark

Add PubMedQA or similar scientific QA benchmark.

Reason:

NeuroEvoScientist should demonstrate task-dependent evolution.

Expected:

GSM8K may favor reasoning-heavy architectures.

Scientific QA may favor memory/retrieval architectures.

---

# Task 4: Re-run Evolution

After substrate activation:

Run:

- GSM8K
- PubMedQA

Compare:

- Fixed architectures
- Random Search
- Evolution without Pareto
- ENSS

---

# Success Criteria

1. Different tasks produce different evolved architectures.
2. Memory genes influence actual model computation.
3. ENSS advantage is not only from prompt templates.
4. Results support the neural substrate evolution claim.

---

# Important Restriction

Do not increase population size or model scale yet.

Do not move to Qwen7B before substrate activation is verified.

The current bottleneck is scientific validity, not compute.
