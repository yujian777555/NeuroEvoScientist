"""V2 paper figures — reproducible from immutable F1/F2 artifacts ONLY.

Inputs:
  v2_quality/fasttrack/f1_results/f1_summary.csv        (F1 dev cells)
  v2_quality/fasttrack/f2_results/run_manifest.json     (F2 locked SVAMP cells)
  v2_quality/fasttrack/f2_results/f2_statistics.json    (F2 paired stats)
  F1 paired stats transcribed from committed v2_quality/fasttrack/f1_results.md

Outputs: figures/fig1_capability_cost.png, figures/fig2_paired_diffs.png
No V1 landscape figures are reused; nothing from paper/phase21_tables.md.
"""

import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FT = os.path.join(HERE, "..", "fasttrack")
FIG = os.path.join(HERE, "figures")

GSM8K_DEV = ["F1-06", "F1-05", "F1-01", "F1-04", "F1-03", "F1-02", "F1-07"]
STYLE = {"REF": ("tab:red", "D", 90), "B2": ("tab:blue", "s", 70),
         "B1": ("tab:green", "o", 70)}


def load_f1():
    rows = list(csv.DictReader(open(os.path.join(
        FT, "f1_results", "f1_summary.csv"), encoding="utf-8")))
    out = []
    for r in rows:
        if r["cell_id"] in GSM8K_DEV:
            out.append((r["baseline"], int(r["prompt_tokens_total"]),
                        float(r["capability"])))
    return out


def load_f2():
    man = json.load(open(os.path.join(FT, "f2_results", "run_manifest.json"),
                         encoding="utf-8"))
    out = []
    for c in man["cells"]:
        out.append((c["config"],
                    c["prompt_tokens_total"] + c["completion_tokens_total"],
                    c["capability"]))
    return out


def fig1():
    f1, f2 = load_f1(), load_f2()
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    for ax, data, title, xlab in (
            (axes[0], f1, "(a) GSM8K dev (F1, n=100)",
             "prompt tokens (thousands)"),
            (axes[1], f2, "(b) SVAMP locked test (F2, n=300)",
             "prompt + completion tokens (thousands)")):
        for name, tok, acc in data:
            color, marker, size = STYLE.get(name, ("tab:gray", "^", 55))
            ax.scatter(tok / 1000.0, 100 * acc, c=color, marker=marker,
                       s=size, zorder=3)
            if name == "REF" and ax is axes[0]:
                ax.annotate(name, (tok / 1000.0, 100 * acc),
                            textcoords="offset points", xytext=(-4, -15),
                            ha="center", fontsize=8)
            else:
                ax.annotate(name, (tok / 1000.0, 100 * acc),
                            textcoords="offset points", xytext=(0, 7),
                            ha="center", fontsize=8)
        ax.set_xlabel(xlab, fontsize=9)
        ax.set_ylabel("accuracy (%)", fontsize=9)
        ax.set_title(title, fontsize=10)
        ax.grid(alpha=0.3, zorder=0)
        ax.tick_params(labelsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_capability_cost.png"), dpi=200)
    plt.close(fig)


def fig2():
    # F1 entries transcribed from committed f1_results.md (paired stats table)
    rows = [
        ("F1 GSM8K dev\nREF $-$ B2 (n=100)", 1.0, -8.0, 10.0, "p=1.00"),
        ("F1 GSM8K dev\nREF $-$ B1 (n=100)", 10.0, 0.0, 20.0, "p=0.087"),
        ("F2 SVAMP test\nREF $-$ B2 (n=300, primary)", -1.33, -6.0, 3.33,
         "p=0.67"),
        ("F2 SVAMP test\nREF $-$ B1 (n=300, secondary)", 0.0, -5.33, 5.33,
         "p=1.00"),
    ]
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    ys = list(range(len(rows)))[::-1]
    for y, (label, d, lo, hi, p) in zip(ys, rows):
        color = "tab:blue" if "F1" in label else "tab:red"
        ax.plot([lo, hi], [y, y], color=color, lw=2.5, zorder=2,
                solid_capstyle="round")
        ax.scatter([d], [y], color=color, s=55, zorder=3)
        ax.text(hi + 1.2, y, "%+.2f pp  %s" % (d, p), va="center",
                fontsize=8)
        ax.text(-23.5, y, label, va="center", ha="left", fontsize=8)
    ax.axvline(0, color="k", lw=0.8, ls="--", alpha=0.6)
    ax.set_xlim(-24, 30)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_yticks([])
    ax.set_xlabel("paired accuracy difference (percentage points, 95% CI)",
                  fontsize=9)
    ax.tick_params(labelsize=8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_paired_diffs.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    fig1()
    fig2()
    print("figures written to", FIG)
