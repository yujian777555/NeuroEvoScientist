"""Statistics for the Phase-2 D2 gate (protocol v5 sections 2 and 4).

Per-item utility at the locked exploratory lambda:

    u_i(c) = correct_i(c) - lambda * (prompt_tokens_i(c) + completion_tokens_i(c)) / 10000

Primary pass/fail uses paired percentile bootstrap 95% CIs (lower bound > 0),
plus a SHUFFLE/RANDOM mid-rank percentile gate (>= 0.95). Exact McNemar on
binary accuracy and the accuracy-token Pareto front are mandatory secondary
outcomes. Any missing/invalid required outcome yields INCOMPLETE/INVALID; a
null with too few valid replicates (M < 950) yields INCONCLUSIVE_NULL, never
PASS. No result is fabricated; failures are reported.
"""

from __future__ import annotations

import hashlib
from math import comb

import numpy as np

# --- Locked constants (protocol sections 2, 3.4, 4) --------------------------
LAMBDA = 0.1            # locked primary price; sensitivity at {0.05, 0.2} only
LAMBDA_SENSITIVITY = (0.05, 0.2)
TOKEN_SCALE = 10000.0   # utility token denominator
BOOT_N = 10000
S0 = 20261021           # locked master seed
ALPHA = 0.05            # per-test level; percentile 95% CI
MIDRANK_THRESHOLD = 0.95
MIN_VALID_REPLICATES = 950  # M < 950 => INCONCLUSIVE_NULL

# --- Run / gate status strings (exact protocol wording) ----------------------
STATUS_PASS = "PASS"
STATUS_INCOMPLETE = "INCOMPLETE"
STATUS_INCOMPLETE_INVALID = "INCOMPLETE/INVALID"
STATUS_INCONCLUSIVE_NULL = "INCONCLUSIVE_NULL"
STATUS_NO_GO_SIMPLE_FEAT = "NO-GO_IDENTICAL_TO_SIMPLE-FEAT"


def per_item_utility(correct, prompt_tokens, completion_tokens, lambda_=LAMBDA):
    """u = correct - lambda * (prompt + completion) / 10000."""
    return (float(correct)
            - lambda_ * (float(prompt_tokens) + float(completion_tokens))
            / TOKEN_SCALE)


def utility_matrix(records, lambda_=LAMBDA):
    """(n_items, n_configs) utility matrix from frozen outcome records.

    ``records[i][c]`` is a mapping with ``correct``, ``prompt_tokens`` and
    ``completion_tokens``. Config column order follows the first record.
    """
    if not records:
        return []
    configs = list(records[0].keys())
    return [[per_item_utility(records[i][c]["correct"],
                              records[i][c]["prompt_tokens"],
                              records[i][c]["completion_tokens"], lambda_)
             for c in configs] for i in range(len(records))]


def quantile_type7(sorted_vals, p):
    """Type-7 (linear, R-7 / numpy 'linear') quantile of pre-sorted values.

    Implemented directly so the result is identical across numpy versions.
    """
    vals = list(sorted_vals)
    n = len(vals)
    if n == 0:
        raise ValueError("quantile of empty sequence")
    if n == 1:
        return float(vals[0])
    h = (n - 1) * float(p)
    lo = int(h)
    if lo >= n - 1:
        return float(vals[-1])
    frac = h - lo
    return float(vals[lo]) + frac * (float(vals[lo + 1]) - float(vals[lo]))


# --- Locked deterministic PRNG (protocol v6 section 4.6, R5-E) ---------------
# All permutation/resampling randomness is NumPy PCG64 inside a
# numpy.random.Generator, seeded per (label, replicate) by
# int.from_bytes(sha256(UTF8(label + "|" + S0 + "|" + r))[:8], "big").
BOOTSTRAP_LABEL = "bootstrap-leval"


def stream_seed(label, r, s0=S0):
    """64-bit unsigned seed for one labeled stream/replicate (exact bytes)."""
    digest = hashlib.sha256(("%s|%s|%s" % (label, s0, r)).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def stream_generator(label, r, s0=S0):
    """A fresh ``numpy.random.Generator(PCG64(seed))`` per (stream, replicate)."""
    return np.random.Generator(np.random.PCG64(stream_seed(label, r, s0)))


def bootstrap_indices(n_items, n_resamples=BOOT_N, seed=S0):
    """Paired resample indices (n_resamples x n_items), PCG64 per replicate.

    Replicate ``r`` (1-based) uses a fresh generator seeded from the stream
    label ``bootstrap-leval``; one index vector is drawn per replicate and is
    reused for every configuration in that paired contrast.
    """
    return [stream_generator(BOOTSTRAP_LABEL, r, seed)
            .integers(0, n_items, size=n_items).tolist()
            for r in range(1, n_resamples + 1)]


def bootstrap_means(diffs, indices):
    """Bootstrap resample means of per-item paired differences (unsorted)."""
    diffs = list(diffs)
    return [sum(diffs[j] for j in row) / len(row) for row in indices]


def paired_bootstrap_ci(diffs, n_resamples=BOOT_N, seed=S0, alpha=ALPHA):
    """Two-sided percentile 95% CI for a paired mean difference.

    Returns ``(lo, hi, means)`` with type-7 quantile interpolation over the
    sorted bootstrap means. The pass rule is ``lo > 0``.
    """
    diffs = list(diffs)
    if not diffs:
        raise ValueError("bootstrap requires at least one item")
    indices = bootstrap_indices(len(diffs), n_resamples, seed)
    means = sorted(bootstrap_means(diffs, indices))
    lo = quantile_type7(means, alpha / 2.0)
    hi = quantile_type7(means, 1.0 - alpha / 2.0)
    return lo, hi, means


def bootstrap_pass(diffs, n_resamples=BOOT_N, seed=S0, alpha=ALPHA):
    """True when the percentile-CI lower bound is strictly greater than 0."""
    lo, _, _ = paired_bootstrap_ci(diffs, n_resamples, seed, alpha)
    return lo > 0.0, lo


def midrank_percentile(null_values, candidate):
    """Mid-rank percentile ``(#< + 0.5 * #==) / M`` of candidate under the null."""
    null_values = list(null_values)
    m = len(null_values)
    if m == 0:
        raise ValueError("mid-rank percentile requires a non-empty null")
    below = sum(1 for v in null_values if v < candidate)
    equal = sum(1 for v in null_values if v == candidate)
    return (below + 0.5 * equal) / m


def mcnemar_exact(a, b):
    """Two-sided exact McNemar on paired binary scores (secondary outcome).

    ``a``/``b`` are per-item binary (0/1) sequences over the same items.
    """
    a, b = list(a), list(b)
    if len(a) != len(b):
        raise ValueError("McNemar requires paired sequences of equal length")
    a_wins = sum(1 for x, y in zip(a, b) if x > y)
    b_wins = sum(1 for x, y in zip(a, b) if x < y)
    n = a_wins + b_wins
    if n == 0:
        return {"discordant": 0, "a_wins": 0, "b_wins": 0, "p_exact": 1.0}
    k = min(a_wins, b_wins)
    p = 2.0 * sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return {"discordant": n, "a_wins": a_wins, "b_wins": b_wins,
            "p_exact": min(1.0, p)}


def pareto_front(points):
    """Non-dominated configs of the accuracy-token Pareto (secondary outcome).

    ``points`` maps config name -> ``(accuracy, total_tokens)``. Accuracy is
    maximized and tokens minimized; a point is dominated when another has
    >= accuracy and <= tokens with at least one strict. Returns the sorted
    list of non-dominated config names.
    """
    names = list(points.keys())
    keep = []
    for name in names:
        acc, tok = points[name]
        dominated = False
        for other in names:
            if other == name:
                continue
            o_acc, o_tok = points[other]
            if (o_acc >= acc and o_tok <= tok
                    and (o_acc > acc or o_tok < tok)):
                dominated = True
                break
        if not dominated:
            keep.append(name)
    return sorted(keep)


def outcomes_complete(records, required_configs):
    """True when every required config has a valid outcome on every item.

    A wrong answer (``correct == 0``) is valid; only missing/non-finite raw
    completion, score, or token counts make an item invalid. Returns
    ``(complete, missing_count)``.
    """
    missing = 0
    for rec in records:
        for c in required_configs:
            o = rec.get(c) if isinstance(rec, dict) else None
            if o is None:
                missing += 1
                continue
            if o.get("raw_completion") is None:
                missing += 1
                continue
            correct = o.get("correct")
            if correct is None or not (correct == 0 or correct == 1
                                       or correct == 0.0 or correct == 1.0):
                missing += 1
                continue
            for key in ("prompt_tokens", "completion_tokens"):
                v = o.get(key)
                if v is None or not isinstance(v, (int, float)) or v != v:
                    missing += 1
                    break
    return (missing == 0, missing)


def confirmatory_status(records, required_configs):
    """INCOMPLETE/INVALID when any required outcome is missing, else PASS-able."""
    complete, missing = outcomes_complete(records, required_configs)
    if not complete:
        return STATUS_INCOMPLETE_INVALID, missing
    return None, 0


def null_gate_status(n_valid_replicates, min_valid=MIN_VALID_REPLICATES):
    """INCONCLUSIVE_NULL when too few valid replicates, else None (scoreable)."""
    if n_valid_replicates < min_valid:
        return STATUS_INCONCLUSIVE_NULL
    return None
