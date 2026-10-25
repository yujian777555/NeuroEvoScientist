"""Phase-2 G1 learnability & pilot pipeline (TACC controller).

Deterministic, document-locked implementation of the v5 protocol
(`plans/phase2_g1_revised_protocol.md`). No GPU, inference, dataset access,
or lock artifacts are exercised by importing this package; the heavy paths in
`pilot.py` are dependency-injected and only run under explicit authorization.

Modules:
- ids:         canonical `src:`/`q:` IDs, hash ordering, partitions/subsets/folds
- features:    frozen HashingVectorizer contract + F0 surface features + shift
- policy:      ridge/logistic/GBT policies, common realized-utility selection
- stats:       utility, paired bootstrap (type-7), mid-rank, McNemar, Pareto
- preflight:   GSM8K JSONL loader, overlap guards, lock/manifest writers
- permutation: namespaced deterministic Fisher-Yates null replay
- pilot:       two-stage runner skeleton (FIT+TUNE -> selection -> LEVAL)
"""

from . import ids, features, stats, policy, preflight, permutation, pilot  # noqa: F401

__all__ = [
    "ids",
    "features",
    "stats",
    "policy",
    "preflight",
    "permutation",
    "pilot",
]
