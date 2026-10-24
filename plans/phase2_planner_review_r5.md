# Phase-2 Planner Review R5 — R4 substantially accepted; remaining protocol ambiguities block CPU preflight

Date: 2026-10-24
Repository: https://github.com/yujian777555/NeuroEvoScientist
Reviewed substantive Executor commit: `87c5c106caaa89eda325f3d9a6479abf30591950`
Reviewed R4 status-only commit: `c80d90d4d8901c2e110680751ddb2b02c4eed09f`
Observed remote `main` HEAD at start of R5 review: `c80d90d4d8901c2e110680751ddb2b02c4eed09f`

## Decision

**CONDITIONAL HOLD. R4-A…R4-H are substantially addressed, but protocol v5 still has reproducibility and comparator/null-definition gaps. CPU preflight and GPU Pilot remain unauthorized.** This is a static review of the current GitHub protocol, decision report, status, and the R4 substantive diff. The Executor's document checks are reported as such; they were not independently rerun in this review.

## 1. Accepted R4 work

- Unified policy/action interface and realized-utility selection across model classes.
- F0 early NO-GO before LEVAL, with no baseline substitution.
- Full adaptive pipeline replay for SHUFFLE, with within-item configuration outcome vectors kept paired.
- Utility at locked λ=0.1 as primary D2 gate; raw accuracy/tokens/Pareto reported separately.
- Missing/invalid LEVAL outputs invalidate the confirmatory run rather than deleting items.
- Bootstrap interval method, resample count, seed, and type-7 interpolation specified.
- The 7,473 partition counts and 500/200/300 pilot subsets remain planned only; no locks were created.
- The 55-minute wall-clock fail-safe remains separate in wording from measured GPU-active time; the ≤1.0 aggregate GPU-hour request remains unapproved.
- Plain TACC remains PIVOT; DEFLECT and MEMROUTE novelty remain NOT CLEARED.

## 2. Remaining blockers

### R5-A — SIMPLE-FEAT reuses thresholds from the wrong feature/score space

Protocol §3.1 defines δ in the selected model's score units and τ from shift-score percentiles in the corresponding feature space. Yet §3.3 says SIMPLE-FEAT uses the candidate's same frozen δ/τ while switching to F0, including an F0-only shift detector. F0 model scores and F0 shift distances are not generally on the same scales as the F1 model/embedding space. Therefore the baseline is not fully defined as a fair F0-only pipeline.

**Required fix:** keep the selected class/hyperparameters frozen, but define separate F0-only TUNE thresholds for SIMPLE-FEAT using the same predeclared δ grid and F0-specific τ candidates. Define its tie-break and final FIT-only fit. The F1 candidate must use its own F1-TUNE-selected thresholds. Both are frozen before LEVAL. Do not reuse F1 τ/δ for F0 unless a scale-invariance argument is demonstrated and testable from the protocol.

### R5-B — fallback ID construction has a prefix ambiguity

Protocol §1.1 says to prefix the normalized fallback with `q:`, but also says “the fallback value is `q:` + SHA-256(question\0 + normalized_question_text).” Read literally, this can create `q:q:<hash>`; it is unclear whether the hash or question text is the normalized value before prefixing.

**Required fix:** define the exact canonical ID once, for example:
- source ID: `src:` + normalized source scalar;
- fallback ID: `q:` + lowercase SHA-256 hex of UTF-8 bytes for `question\0` + normalized question text.
State that the `q:` namespace prefix is applied exactly once. Define precisely how missing/unusable IDs trigger fallback. Do not generate IDs or lock files in this round.

### R5-C — embedding and hand-feature extraction are not reproducibly locked

The protocol refers to a “frozen query embedding”, while the controller design only suggests a “small frozen encoder (e.g. a MiniLM-class sentence encoder)”. The confirmatory feature F1 is therefore not reproducible yet. F0 also says “question length” and “numeric density” without a fully exact computation contract.

**Required fix:** document, without downloading/loading the model or data:
- exact embedding model identifier and immutable revision/weight hash;
- tokenizer version, text normalization, truncation/max length, pooling, output normalization and embedding dimension;
- exact definition of question length (character/codepoint or tokenizer token count);
- exact numeric-token matching rule and numeric-density denominator;
- required package/runtime versions and how the frozen embedding outputs will be hashed/validated.
If these cannot be fixed before preflight, do not treat F1 or its confirmatory results as reproducible; keep the gate closed.

### R5-D — SHUFFLE drops F0-selected replicates without defining the conditional test

Protocol §3.4 marks a permutation replicate that selects F0 as NO-GO and does not score it, then computes the percentile over only valid replicates. This makes the null distribution conditional on selecting F1. That may be defensible because the observed candidate proceeds only after selecting F1, but the protocol does not name the conditional estimand or explain the interpretation. The proportion of F0-selected replicates is also not explicitly a mandatory reported diagnostic.

**Required fix:** explicitly define the SHUFFLE test as conditional on the replicate selecting F1, justify why this conditioning matches the observed candidate's F1 selection event, and require reporting counts/proportion for F0-NO-GO, other invalid replicates, and scored F1 replicates. Keep `M < 950 => INCONCLUSIVE_NULL`. If a defensible conditional interpretation cannot be established, choose a predeclared alternative statistic for no-go replicates before LEVAL; do not silently exclude them or alter the denominator after seeing outcomes.

### R5-E — permutation determinism and compute accounting are underspecified

The protocol gives Fisher–Yates plus an integer seed, but does not identify the PRNG algorithm/runtime that turns that seed into random integers. It also calls the workload “103 small model fits” while a ridge/GBT policy contains one regressor per non-B1 action; the number of underlying estimator fits is therefore not 103. The four-CPU-hour timeout is explicitly provisional, which is appropriate, but the counting unit must be clear.

**Required fix:** specify the exact PRNG and version/algorithm (or use a fully specified hash-based deterministic permutation algorithm), including seed-to-stream derivation. Distinguish policy-fit invocations from individual estimator fits and revise the workload description accordingly. Keep the two-replicate smoke test and any CPU preflight unauthorized until separately approved.

### R5-F — majority-action tie rule points to the wrong rule

Protocol §4.1 says MAJORITY frequency ties are “ties per §2”, but §2 defines how to break utility ties for each item's best action, not how to break a tie between action frequencies across FIT items.

**Required fix:** explicitly state that if multiple configurations have the same highest best-action frequency, the tie is broken by the fixed configuration order `(B1, B0, B3, REF, B2)` (or another predeclared rule). Remove the ambiguous cross-reference.

### R5-G — define the scope of the 55-minute wall-clock fail-safe versus CPU null analysis

The 55-minute fail-safe is described in the pilot budget, while the SHUFFLE procedure may require up to 1,000 adaptive CPU replays and a provisional four-CPU-hour timeout. State unambiguously that the 55-minute/60-minute cap applies to the GPU inference/data-collection phase, and define the separately authorized CPU-analysis timeout/checkpoint policy. Do not combine the phases into one impossible wall-clock promise or imply the CPU work is included in the GPU-hour budget.

## 3. Authorization boundary

- GPU authorization: **0**.
- Controller implementation/training/inference: **not authorized**.
- Dataset download/loading and partition/subset lock generation: **not authorized**.
- CPU preflight and the two-replicate smoke test: **not authorized**.
- MATH-500: untouched.
- Frozen V1/V2 papers, PDFs, supplements, and historical F1/F2 results must remain untouched.

Only document-only R5 repairs are authorized. After pushing, stop for Planner R6 review. CPU preflight and GPU Pilot each require separate explicit approval.

## 4. R5 verdict

**R4 substantially accepted; protocol v5 needs a final document-only consistency pass before CPU preflight. No experiment is authorized.**
