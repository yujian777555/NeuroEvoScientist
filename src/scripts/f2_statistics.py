"""F2 statistics: paired bootstrap + exact McNemar on SVAMP confirmation.

Primary contrast:   REF vs B2 (strongest CoT-matched preset).
Secondary contrast: REF vs B1 (no-memory CoT control).

Algorithm identical to src/scripts/phase20_statistics.py
(BOOT_N=10000, BOOT_SEED=20260923, two-sided exact McNemar);
SVAMP item scores are binary accuracy, so McNemar is applicable.

Reads  v2_quality/fasttrack/f2_results/predictions_f2_{REF,B2,B1}.jsonl
Writes v2_quality/fasttrack/f2_results/f2_statistics.json
"""

import json
import os
import random
from math import comb

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
RESULTS = os.path.join(REPO, "v2_quality", "fasttrack", "f2_results")

BOOT_N = 10000
BOOT_SEED = 20260923  # same fixed seed as Phase-19/20/F1 statistics


def load(name):
    table = {}
    with open(os.path.join(RESULTS, "predictions_f2_%s.jsonl" % name),
              encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            table[r["svamp_id"]] = r["correct"]
    return table


def paired_bootstrap(a, b, n=BOOT_N, seed=BOOT_SEED):
    rng = random.Random(seed)
    items = sorted(set(a) & set(b))
    diffs = [a[i] - b[i] for i in items]
    means = []
    for _ in range(n):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        means.append(sum(sample) / len(sample))
    means.sort()
    acc_a = sum(a[i] for i in items) / len(items)
    acc_b = sum(b[i] for i in items) / len(items)
    return {"n_items": len(items), "score_a": round(acc_a, 4),
            "score_b": round(acc_b, 4),
            "diff_pp": round(100 * (acc_a - acc_b), 2),
            "ci95_lo_pp": round(100 * means[int(0.025 * n)], 2),
            "ci95_hi_pp": round(100 * means[int(0.975 * n)], 2)}


def mcnemar(a, b):
    items = sorted(set(a) & set(b))
    aw = sum(1 for i in items if a[i] > b[i])
    bw = sum(1 for i in items if a[i] < b[i])
    n = aw + bw
    if n == 0:
        return {"discordant": 0, "a_wins": 0, "b_wins": 0, "p_exact": 1.0}
    k = min(aw, bw)
    p = 2 * sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return {"discordant": n, "a_wins": aw, "b_wins": bw,
            "p_exact": round(min(1.0, p), 6)}


def main():
    ref, b2, b1 = load("REF"), load("B2"), load("B1")
    assert len(ref) == len(b2) == len(b1) == 300

    out = {
        "dataset": "SVAMP test (300 locked items)",
        "method": ("paired bootstrap 95%% CI (n=%d, seed=%d) + two-sided "
                   "exact McNemar (binary accuracy)" % (BOOT_N, BOOT_SEED)),
        "primary_contrast": {
            "name": "REF vs B2",
            "bootstrap": paired_bootstrap(ref, b2),
            "mcnemar": mcnemar(ref, b2),
        },
        "secondary_contrast": {
            "name": "REF vs B1",
            "bootstrap": paired_bootstrap(ref, b1),
            "mcnemar": mcnemar(ref, b1),
        },
        "descriptive_B2_vs_B1": {
            "name": "B2 vs B1 (descriptive only, not pre-registered)",
            "bootstrap": paired_bootstrap(b2, b1),
            "mcnemar": mcnemar(b2, b1),
        },
    }
    path = os.path.join(RESULTS, "f2_statistics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
