# Phase-20 Hotfix Gate — Semantic and Reproducibility Corrections

## Why this hotfix exists

Planner review of commit `c772108` found several claim-critical issues that must be corrected **before any Phase-20 matrix result is treated as paper evidence**.

The structured-search direction is valid, but the current implementation has mismatches between names, normalization, and actual computation.

## H1 — Make hashed embeddings truly deterministic

Current `hashed_embedding()` uses Python's built-in `hash(tok)`, which is randomized across interpreter processes unless `PYTHONHASHSEED` is externally fixed. This invalidates the docstring's "deterministic" claim and can create run-to-run changes in dense retrieval / Mamba2 memory inputs.

Required fix:
- replace `hash(tok)` with a stable digest (e.g. SHA-256 / BLAKE2-based integer mapping);
- add a subprocess regression test showing identical embeddings across two independent Python processes;
- bump Phase-20 cache/schema version so old cached results are not mixed with corrected embeddings.

## H2 — Remove duplicate no-memory phenotypes

With `exemplar_count=0`, recency/retrieval/hybrid/mamba2 all inject no exemplars, yet `memory_type` remains in `phenotype_hash()`. Therefore multiple effectively identical no-memory inference phenotypes are counted as distinct architectures.

Required fix:
- canonicalize the no-exemplar case to one explicit effective phenotype, e.g. `memory_type="none"`, OR exclude memory fields from the phenotype hash when `exemplar_count=0`;
- if adaptation remains enabled while no memory is used, decide explicitly whether adaptation cost is part of the phenotype. Prefer disabling memory adaptation when `exemplar_count=0`;
- add tests that equivalent no-memory genomes produce the same phenotype hash.

## H3 — Fix verifier_passes=0 semantics

Current prompt helper treats `verifier_passes=0` as falsy and falls back to the default phrase "step by step", so 0 does not mean 0 passes.

Required fix:
- either remove 0 from the search space and use `[1,2,3]`, or implement an explicit zero-pass semantic;
- add exact prompt tests for every verifier_passes value.

## H4 — QASPER context-budget claim is not currently implemented

QASPER currently truncates the paper context to a fixed `max_context_words=2500` independent of the genome. The Phase-20 `token_budget` gene only affects recalled exemplars.

Therefore the current implementation cannot support the preregistered claim that QASPER tests genome-controlled long-document context allocation.

Required fix:
- introduce a real genome-controlled input/evidence budget (separate from exemplar verbosity), e.g. `input_context_budget`;
- apply it to the QASPER paper context before prompt construction;
- keep exemplar policy separate from document/evidence budget;
- if this is not implemented, rewrite the QASPER hypothesis to only test reasoning/exemplar behavior and do not claim long-context budget co-design.

Because this is detected before paper-facing holdout analysis, amend the QASPER preregistration **before rerunning corrected QASPER experiments**. Existing QASPER Phase-20 results under the old semantics must be tagged invalid for paper evidence.

## H5 — Rename or replace "dense" retrieval

Current `dense` retrieval is cosine similarity over hashed bag-of-words vectors. It is not a learned semantic dense retriever.

Choose one:
1. rename it accurately to `hashed_bow` / `hashed_dense_lexical`; or
2. implement a real embedding-based dense retriever.

Do not use the generic paper-facing term "dense retrieval" for the current hash-BOW implementation.

## H6 — Use the actual LongBench QASPER normalization

The current local `qa_f1()` does not match LongBench's standard QA F1 normalization: LongBench lowercases, removes punctuation, removes English articles, fixes whitespace, then computes token F1.

Required fix:
- copy/reimplement the LongBench normalization exactly;
- add unit tests against known examples;
- state clearly whether evaluation uses the whole generated response or only the extracted final answer. If using the `####` suffix, call the metric "LongBench-compatible normalized QA F1 on extracted final answer", not an unqualified "official LongBench score".

## Matrix handling

Until H1-H6 are resolved:
- do not promote current Phase-20 QASPER runs to paper evidence;
- do not aggregate mixed pre-hotfix and post-hotfix caches;
- invalidate/restart any Phase-20 run whose output depends on the changed stable hash / phenotype semantics;
- GSM8K/PubMedQA results may be reused only if a result-level audit proves the corrected code would produce identical prompts, substrates, and metrics. Otherwise rerun.

## Verification gate

Before resuming the paper-facing Phase-20 matrix, require:
- stable embeddings across processes;
- no duplicate effective no-memory phenotypes;
- verifier-pass semantics exact;
- genome-controlled QASPER input-context budget OR a downgraded preregistered claim;
- honest retrieval metric naming;
- LongBench-compatible normalized QASPER F1;
- cache/schema version bumped;
- all tests green.

## Paper-claim rule

C3 and C5 remain permanently closed. This hotfix is not an attempt to recover them.

Phase-20 remains focused on:
1. stronger task-conditioned cognitive architecture evidence;
2. a genuinely distinct third task;
3. interpretable mechanism analysis;
4. reproducible structured co-design.

Suggested executor commit message:

`[Phase-20 hotfix] correct structured phenotype semantics and QASPER evaluation`
