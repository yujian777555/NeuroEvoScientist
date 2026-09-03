# Phase-13 ENSS Upgrade Plan

## Review Summary

Phase-12 successfully implemented the MVP evolution loop:

Genome -> Agent Builder -> Evaluation -> Fitness -> Evolution

However, the current implementation is only a validation prototype.
The MockEvaluator signal is too strong and cannot support paper claims.

## Goal

Upgrade ENSS from a demo evolutionary loop into a research-grade evolutionary agent architecture search framework.

## Tasks

### Task 1: Replace synthetic evaluation with real benchmark interface

Priority:
High

Implement:

- src/evaluator/gsm8k.py
- benchmark adapter interface
- real task scoring pipeline

Requirements:

- Keep MockEvaluator for CI testing only.
- Do not use MockEvaluator for paper results.

Future support:

- GSM8K
- AgentBench
- PubMedQA

---

### Task 2: Implement Weight Inheritance

Priority:
High

Add:

src/evolution/inheritance.py

Goal:

Parent Agent weights/features should partially transfer to child architectures.

Required interface:

Parent Genome
+
Parent State

->

Child Genome
+
Inherited State


Reason:

Reduce evolution cost on A800 experiments.

---

### Task 3: Upgrade Search Space

Current:

8 architectures

Upgrade gradually:

Memory:
- attention
- mamba
- retrieval
- hybrid

Reasoning:
- direct
- verify
- planner
- cot

Compression:
- none
- lora
- qlora
- int8

Target:
64+ architectures.

---

### Task 4: Verify NSGA-III implementation

Check:

- non-dominated sorting
- Pareto front generation
- diversity preservation
- multi-objective selection

Avoid reducing ENSS into single-score genetic search.

---

## Verification

Success criteria:

1. Real benchmark can replace MockEvaluator without changing evolution controller.
2. Evolution supports inherited child states.
3. Search space is larger than MVP.
4. Multi-objective Pareto optimization is clearly implemented.

## Constraints

Do not change the paper direction.
Do not simplify ENSS into ordinary NAS.
Do not remove Mamba memory exploration.

Wait for Planner review before major algorithm changes.
