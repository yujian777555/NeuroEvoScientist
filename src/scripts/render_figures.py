"""Render final paper figures from committed result artifacts (Phase-21).

Outputs PNG (300 dpi) into paper/figures/:
- fig2_gene_distributions.png   per-task converged genes (3 seeds, dev)
- fig3_transfer_matrix.png      holdout capability matrix, own vs cross
- fig4_qasper_diag.png          F1 extracted vs whole + marker compliance
- fig5_memory_ablation.png      controlled ablation across backbones
- fig6_landscape_pareto.png     48-point landscape capability vs tokens

Run: python src/scripts/render_figures.py
"""

import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(_REPO, "paper", "figures")
plt.rcParams.update({"figure.dpi": 300, "font.size": 9})


def fig_gene_distributions():
    lock = json.load(open(os.path.join(_REPO, "results",
                                       "phase20_selection_lock.json")))
    reps = {}
    for c in lock["configurations"][:3]:
        reps[c["name"].replace("A_", "")] = c["genome"]
    tasks = list(reps)
    genes = ["memory_type", "reasoning", "context_mode", "exemplar_count",
             "input_context_budget"]

    fig, ax = plt.subplots(figsize=(6.0, 2.4))
    ax.axis("off")
    cell_text = [[reps[t][g] for t in tasks] for g in genes]
    table = ax.table(cellText=cell_text,
                     rowLabels=genes, colLabels=tasks,
                     cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.4)
    ax.set_title("Converged genes per task (dev search, 3 seeds)", pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_gene_distributions.png"))
    plt.close(fig)


def fig_transfer_matrix():
    import csv
    rows = list(csv.DictReader(open(os.path.join(
        _REPO, "results", "phase20_holdout_results.csv"))))
    reps = ["A_gsm", "A_pubmed", "A_qasper"]
    benches = ["gsm8k", "pubmedqa", "qasper"]
    for model_tag, suffix in (("1.5B", "15b"), ("7B", "7b")):
        M = np.zeros((3, 3))
        for i, cfg in enumerate(reps):
            for j, bench in enumerate(benches):
                hit = [r for r in rows if r["config"] == cfg
                       and r["benchmark"] == bench and model_tag in r["model"]]
                M[i, j] = float(hit[0]["capability"]) if hit else np.nan
        fig, ax = plt.subplots(figsize=(3.6, 3.0))
        im = ax.imshow(M, cmap="viridis", vmin=0, vmax=0.9)
        ax.set_xticks(range(3), benches, rotation=20)
        ax.set_yticks(range(3), reps)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, "%.2f" % M[i, j], ha="center", va="center",
                        color="white" if M[i, j] < 0.5 else "black",
                        fontsize=8)
        ax.set_title("Holdout capability (%s)" % model_tag)
        fig.colorbar(im, ax=ax, shrink=0.8)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "fig3_transfer_matrix_%s.png" % suffix))
        plt.close(fig)


def fig_qasper_diag():
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.6), sharey=True)
    for ax, tag, title in ((axes[0], "15b", "Qwen2.5-1.5B"),
                           (axes[1], "7b", "Qwen2.5-7B")):
        d = json.load(open(os.path.join(_REPO, "results",
                                        "phase21_qasper_diag_%s.json" % tag)))
        names = list(d["configs"])
        ext = [d["configs"][n]["mean_f1_extracted"] for n in names]
        whole = [d["configs"][n]["mean_f1_whole"] for n in names]
        x = np.arange(len(names))
        ax.bar(x - 0.2, ext, 0.4, label="F1 extracted")
        ax.bar(x + 0.2, whole, 0.4, label="F1 whole (diag)")
        ax.set_xticks(x)
        ax.set_xticklabels([n.replace("A_", "A\n").replace("fixed_", "fx\n")
                            for n in names], fontsize=7)
        ax.set_title(title)
        ax.set_ylim(0, 0.25)
        for n, xi, m in zip(names, x,
                            [d["configs"][n]["marker_compliance"]
                             for n in names]):
            ax.text(xi, 0.235, "m=%.2f" % m, ha="center", fontsize=6)
    axes[0].set_ylabel("normalized QA F1")
    axes[1].legend(fontsize=7)
    fig.suptitle("QASPER: extraction vs whole-continuation F1 (m=marker compliance)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig4_qasper_diag.png"))
    plt.close(fig)


def fig_memory_ablation():
    data = [("GSM8K\n(same-genome)", 0.0, 12.55),
            ("PubMedQA\n(controlled)", 18.0, None),
            ("QASPER\n(controlled)", 1.5, None)]
    fig, ax = plt.subplots(figsize=(4.5, 2.8))
    x = np.arange(len(data))
    vals = [d[1] if d[2] is None else d[2] for d in data]
    ax.bar(x, vals, color=["#999999", "#2a9d66", "#2a9d66"])
    for xi, d in zip(x, data):
        top = max(d[1], d[2] or 0)
        if d[2] is None:
            ax.text(xi, top + 0.4, "%+.1fpp" % d[1], ha="center",
                    va="bottom", fontsize=8)
        else:
            ax.text(xi, top + 0.4, "7B: %+.1fpp" % d[2], ha="center",
                    va="bottom", fontsize=8, color="#444")
            ax.text(xi, top + 2.6, "1.5B: %+.1fpp" % d[1], ha="center",
                    va="bottom", fontsize=8, color="#777")
    ax.set_xticks(x)
    ax.set_xticklabels([d[0] for d in data], fontsize=8)
    ax.set_ylabel("memory ON - OFF (pp)")
    ax.set_ylim(0, max(vals) * 1.35)
    ax.set_title("Controlled memory ablation (same frozen genome)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig5_memory_ablation.png"))
    plt.close(fig)


def fig_landscape_pareto():
    fronts = json.load(open(os.path.join(_REPO, "results",
                                         "phase18_pareto_fronts.json")))
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.8))
    for ax, bench in zip(axes, ("gsm8k", "pubmedqa")):
        rows = [json.loads(l) for l in open(os.path.join(
            _REPO, "experiments", "landscape_%s" % bench, "landscape.jsonl"))]
        x = [r["prompt_tokens_total"] / 1000.0 for r in rows]
        y = [r["capability"] for r in rows]
        ax.scatter(x, y, s=8, alpha=0.4, label="48 configs")
        fr = sorted(fronts[bench], key=lambda p: p["capability"])
        fx = [next(r["prompt_tokens_total"] / 1000.0 for r in rows
                   if r["architecture"] == p["architecture"])
              for p in fr]
        fy = [p["capability"] for p in fr]
        ax.plot(fx, fy, "o-", color="crimson", ms=4, lw=1,
                label="Pareto front")
        ax.set_xlabel("prompt tokens (k)")
        ax.set_title(bench)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("capability")
    fig.suptitle("Architecture landscape: capability vs token cost")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig6_landscape_pareto.png"))
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    fig_gene_distributions()
    fig_transfer_matrix()
    fig_qasper_diag()
    fig_memory_ablation()
    fig_landscape_pareto()
    print("figures written to", OUT)


if __name__ == "__main__":
    main()
