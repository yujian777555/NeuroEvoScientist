# Phase2-R1 Independent Lock Audit

Date: 2026-10-26
Scope: read-only independent audit of the R1 duplicate-group partition lock.
No GPU, model inference, API calls, benchmark episodes, or MATH-500 access was used. No production lock, source data, historical NO-GO evidence, frozen thresholds, or historical results were modified.

## Final decision: **REQUEST CHANGES**

The actual partition assignment and detector semantics independently recompute correctly, but one required enforcement behavior fails: changing the embedded duplicate-group membership in a deep-copied lock is **not rejected**. The lock cannot be accepted as fully tamper-enforcing until this gap is fixed and independently re-audited.

This is **not** a NO-GO finding against the currently observed sample assignment itself. It is a request to repair lock-enforcement completeness before Planner approval. GPU Pilot remains unauthorized.

## Exact commits and artifact hashes

- Starting/expected HEAD: `67bc6da9c6a7563767a74330ad5a82e586b6ca16`
- R1 implementation commit: `68a499bc1fefdb767e681bd3c7c5532954e0fb21`
- R1 evidence/status commit: `67bc6da9c6a7563767a74330ad5a82e586b6ca16`
- `phase2/pilot_r1/partition_lock_r1.json` bytes: 4,395,752; SHA-256 `ff6c703e4dce45e88b6847a144433479a1702feae5cf5afc3a466ffd8a5c5035`
- Reproduction lock: `phase2/pilot_r1_reprocheck/partition_lock_r1.json`, same SHA-256 `ff6c703e4dce45e88b6847a144433479a1702feae5cf5afc3a466ffd8a5c5035`
- Duplicate audit and its reproduction: SHA-256 `19129608b6154b35d0c6c6b8421bc96bef8f67e4141524f2829cb9a4c0d0e1ea` (identical in both directories)
- GSM8K train: `17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465`
- GSM8K test: `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`
- Historical NO-GO manifest: `05b0bfe9f8e89278ac292620a5e901ff0f622a5be83fbd3acebdbd2ee18ef49f`
- Historical NO-GO log: `84218672005bd21cf6bb7ec6b25f78b768c92e28a49a36d903d1beebec9a8896`

## Commands run and evidence retained

- `git fetch origin main`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git status --short --branch`
- `git show --stat --summary 68a499b...` and `git show --stat --summary 67bc6da...`; `git diff --name-only` across the two R1 commits
- `sha256sum phase2/pilot_r1/partition_lock_r1.json data/gsm8k/train.jsonl data/gsm8k/test.jsonl phase2/pilot/preflight_manifest.json phase2/pilot/preflight.log`
- Independent inline recompute (not a call to the production validator): `planner/r1_independent_recompute.log`
- Independent deep-copy enforcement checks: `planner/r1_enforcement_checks.log`
- Full CPU suite rerun: `python -m pytest tests/ -q`, evidence `planner/r1_full_pytest.log`

## PASS findings

### Git and artifact integrity

- HEAD and `origin/main` both equal `67bc6da9c6a7563767a74330ad5a82e586b6ca16`; worktree was clean before audit changes.
- The two R1 commits contain only the expected implementation, tests, audit artifacts, and status/manifest updates.
- Independently reading the lock bytes reproduces the expected lock SHA-256 exactly; the expected hash was not merely copied from a manifest.
- Recomputed source hashes match the recorded train/test values.

### Independent partition recomputation

From `planner/r1_independent_recompute.log`:

- Counts: BANK=2,989; FIT=1,868; TUNE=1,121; LEVAL=1,495.
- Independently recomputed partition hashes:
  - BANK `b26f0e1a1ff1824c59a9000a7f83d12fd1f86038bb54a7223646a3618d1244db`
  - FIT `b3b992ec4c4ad9473a97d4b81c1c127ff62fcf97738fdb2a21ea08dc91e14728`
  - TUNE `d2afd774a976c9766a2a343f06af0395c6556a5af0f5058438ce288cec2dcf83`
  - LEVAL `4ec2f7c0f4567ec676fed8e27a259f1722be04d61f9358855dbc090909527400`
- All 7,473 canonical sample IDs occur exactly once; no missing or duplicate assignments.
- Independent DSU recomputation yields 7,472 groups; the only two-member group contains exactly the Josie and Amanda IDs and is entirely in BANK.
- Independently computed near-duplicate edges: 1, at train row indices (2483, 6691), Jaccard 0.9310344827586207. Cross-partition near-duplicate edges after the atomic split: 0.

### Detector semantics

- Jaccard alone determines a duplicate edge. `SequenceMatcher.ratio()` is reported as secondary evidence but is not used as an alternative or combined acceptance rule.
- Jaccard is `|A∩B| / |A∪B|` over lowercase `[a-z0-9]+` token sets. Threshold is 0.9, matching the frozen code and historical NO-GO evidence.
- The length filter is mathematically sound: for token sets A and B, `|A∩B|/|A∪B| ≤ min(|A|,|B|)/max(|A|,|B|)`. Therefore pairs below that upper bound cannot meet the 0.9 threshold and can safely be excluded without losing a qualifying pair.
- The scan is exhaustive, not sampled: all 27,919,128 pairs are accounted for; 5,386,387 are explicitly scored and 22,532,741 are eliminated only by that valid upper bound.
- The non-clique guard rejects a synthetic A–B–C chain (`CHAIN_NON_CLIQUE`), so connected components are not silently accepted through transitive over-merging.
- The exact-count failure path rejects an indivisible 2,990-member group instead of splitting it or silently reducing the dataset.

### Evidence and tests

- Second lock reproduction has the same SHA-256 as the primary lock; duplicate-audit files are also byte-identical across the two runs.
- Historical NO-GO artifacts retain their recorded hashes.
- The R1 test log contains `204 passed`; `phase2_preflight_r1_regression.json` records 204 passed and 0 failed.
- An independent full-suite rerun during this review also completed with **204 passed, 0 failed** (`planner/r1_full_pytest.log`).

## FAIL findings

### Embedded duplicate-group membership is not validated

Independent deep-copy test in `planner/r1_enforcement_checks.log`:

- Source hash change: rejected.
- Partition hash change: rejected.
- Partition membership change: rejected.
- Group assignment change: rejected.
- Detector threshold change: rejected.
- **Embedded group membership change: NOT_REJECTED.**

Specifically, changing the two-member Josie/Amanda entry in `lock["groups"]` to a one-member entry, while leaving `group_assignment` and `partitions` untouched, still returns `True` from `duplicates.validate_lock`.

Root cause: `validate_lock` recomputes the assignment, counts, and partition hashes, but never compares the lock's embedded `groups` list with a recomputed duplicate-group structure. This leaves an integrity gap: a manifest/lock editor could alter the recorded duplicate-group definitions without detection.

Implication: the current evidence proves the observed assignment is correct, but does not prove that every field of the lock is tamper-enforced. The explicit Planner requirement that changing group membership must be rejected is unmet.

## NOT VERIFIED

- The upstream dataset Git commit is not present in existing metadata. Immutable file content hashes were verified; an upstream commit identity was not asserted.
- No GPU Pilot, model accuracy, utility statistics, or end-to-end experimental validity was assessed; those were outside authorization.
- No inference was performed and no new confirmation benchmark was accessed.

## Required change before acceptance

1. Extend lock validation to compare the embedded duplicate-group list against a deterministically recomputed group structure, including member IDs, group sizes, and ambiguity/clique status, and reject any mismatch.
2. Add a regression test for the exact deep-copy case above and rerun the complete suite and this independent audit.

Do not change the current production lock or historical artifacts to force acceptance. A separate Planner decision remains necessary after the repair and re-review.
