"""Bit-reproducible permutation null (protocol v6 section 4.6, R5-D/E).

The SHUFFLE null permutes the *complete* per-config outcome vector among
FIT_pilot items and, independently, among TUNE_pilot items, then replays the
identical adaptive pipeline (FIT CV, feature models, TUNE selection, final
FIT-only refit). Within-item configuration outcomes stay paired; LEVAL
outcomes are only used for final scoring.

All randomness is NumPy PCG64 inside a fresh ``numpy.random.Generator`` per
(stream, replicate), seeded by ``int.from_bytes(sha256(UTF8(label + "|" + S0 +
"|" + r))[:8], "big")`` (see ``stats.stream_generator``). Fisher-Yates draws
``j = generator.integers(0, i + 1)`` for ``i`` from ``n-1`` down to ``1``. FIT
and TUNE use distinct labels and are therefore independent. The same seed on
the pinned NumPy version / 64-bit little-endian platform reproduces the
identical permutation.

A replicate that selects F0 is NO-GO and is not scored (matching the
candidate's guard). The null distribution holds the LEVAL utilities of valid
F1 replicates; PASS requires a mid-rank percentile >= 0.95 with M >= 950
valid replicates, else INCONCLUSIVE_NULL.
"""

from __future__ import annotations

import json

from .stats import (MIDRANK_THRESHOLD, MIN_VALID_REPLICATES, S0,
                    STATUS_INCONCLUSIVE_NULL, midrank_percentile,
                    null_gate_status, stream_generator, stream_seed)

# Locked namespace labels for the independent streams (section 4.6 / 5.2).
NS_SHUFFLE_FIT = "shuffle-fit"
NS_SHUFFLE_TUNE = "shuffle-tune"
NS_RANDOM_POLICY = "random-policy"

N_REPLICATES = 1000
CHECKPOINT_EVERY = 10
SMOKE_REPLICATES = 2  # authorized two-replicate smoke option


def deterministic_permutation(n, namespace, r, s0=S0):
    """Fisher-Yates permutation of ``range(n)`` for one namespaced replicate.

    Returns a list ``perm`` where ``perm[i]`` is the source index placed at
    position ``i`` (apply as ``items[perm[i]]`` or gather by position). Uses a
    fresh PCG64 generator so no cross-replicate state leaks.
    """
    gen = stream_generator(namespace, r, s0)
    perm = list(range(n))
    for i in range(n - 1, 0, -1):
        j = int(gen.integers(0, i + 1))
        perm[i], perm[j] = perm[j], perm[i]
    return perm


def permute_outcome_table(U, tokens, perm):
    """Move the whole per-item outcome vector by ``perm`` (config pairing kept).

    ``U`` / ``tokens`` are ``(n_items, n_configs)`` sequences; row ``i`` of the
    result is row ``perm[i]`` of the input, so feature-outcome association is
    broken while within-item config pairing is preserved.
    """
    return ([list(U[perm[i]]) for i in range(len(perm))],
            [list(tokens[perm[i]]) for i in range(len(perm))])


def null_counts(total, f0_nogo, invalid, valid):
    """Conditional-null reporting counts (R5-D): every replicate accounted for."""
    return {"total": total, "f0_nogo": f0_nogo, "invalid": invalid,
            "valid": valid}


def shuffle_pass(null_utilities, candidate_utility,
                 threshold=MIDRANK_THRESHOLD, min_valid=MIN_VALID_REPLICATES):
    """Mid-rank gate for one candidate against the SHUFFLE null.

    Returns ``(status_or_None, percentile_or_None, M)``. Status is
    INCONCLUSIVE_NULL when M < min_valid; otherwise the percentile is compared
    to ``threshold`` (PASS when >= threshold).
    """
    m = len(null_utilities)
    gate = null_gate_status(m, min_valid)
    if gate is not None:
        return gate, None, m
    pct = midrank_percentile(null_utilities, candidate_utility)
    return (None if pct >= threshold else "FAIL"), pct, m


def run_shuffle_null(replay_fn, n_replicates=N_REPLICATES, s0=S0,
                     checkpoint_path=None, checkpoint_every=CHECKPOINT_EVERY,
                     smoke=None):
    """Run the adaptive SHUFFLE replay and collect the conditional null.

    ``replay_fn(perm_fit, perm_tune, r)`` reruns the full pipeline on permuted
    outcomes and returns either ``{"feature_set": "F0"}`` (NO-GO, unscored),
    ``None`` (invalid replicate), or ``{"feature_set": "F1",
    "leval_utility": float}`` (valid, scored on locked LEVAL outcomes).

    Checkpointing writes progress JSON every ``checkpoint_every`` replicates so
    a partial run is resumable/inspectable and is never presented as complete.
    ``smoke=k`` (the authorized two-replicate smoke test) runs only k
    replicates and is always marked incomplete-for-decision.
    """
    if smoke is not None:
        n_replicates = int(smoke)
    null_utilities = []
    f0_nogo = invalid = 0
    for r in range(1, n_replicates + 1):
        perm_fit = deterministic_permutation(
            _replay_n(replay_fn, "fit"), NS_SHUFFLE_FIT, r, s0)
        perm_tune = deterministic_permutation(
            _replay_n(replay_fn, "tune"), NS_SHUFFLE_TUNE, r, s0)
        try:
            out = replay_fn(perm_fit, perm_tune, r)
        except Exception:
            out = None
        if out is None:
            invalid += 1
        elif out.get("feature_set") == "F0":
            f0_nogo += 1
        else:
            null_utilities.append(float(out["leval_utility"]))
        if checkpoint_path and (r % checkpoint_every == 0):
            _write_checkpoint(checkpoint_path, r, n_replicates, null_utilities,
                              f0_nogo, invalid, s0, smoke)
    m = len(null_utilities)
    return {
        "null_utilities": null_utilities,
        "counts": null_counts(n_replicates, f0_nogo, invalid, m),
        "M": m,
        "gate": null_gate_status(m),
        "smoke": smoke is not None,
        "complete": smoke is None and n_replicates == N_REPLICATES,
        "s0": s0,
    }


def _replay_n(replay_fn, which):
    """FIT/TUNE item counts for permutation, from the replay_fn's metadata."""
    return int(getattr(replay_fn, "n_%s" % which))


def _write_checkpoint(path, done, total, null_utilities, f0_nogo, invalid, s0,
                      smoke):
    payload = {"replicates_done": done, "replicates_total": total,
               "valid": len(null_utilities), "f0_nogo": f0_nogo,
               "invalid": invalid, "s0": s0, "smoke": smoke is not None,
               "complete": False}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
