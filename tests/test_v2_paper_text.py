"""Gate-3 hotfix regression guards: deterministic text checks on the V2
paper sources (main.tex + manuscript.md). No PDF build required."""

import os

REPO = os.path.join(os.path.dirname(__file__), "..")
PAPER = os.path.join(REPO, "v2_quality", "paper")

FORBIDDEN = [
    "pre-registered", "preregistered", "Pre-registered",
    "statistically indistinguishable",
    "ties the strongest", "ties B2",
    "seven presets", "Seven presets", "seven CoT-matched",
    "six CoT presets plus",
    "context budget matters more",
    "no foreseeable misuse",
    "10\u00d7",  # 10×
    "10$\\times$",
]


def _read(name):
    with open(os.path.join(PAPER, name), encoding="utf-8") as f:
        return f.read()


def test_no_forbidden_phrases():
    for name in ("main.tex", "manuscript.md"):
        body = _read(name)
        for phrase in FORBIDDEN:
            assert phrase not in body, "%s contains %r" % (name, phrase)


def test_baseline_count_wording():
    for name in ("main.tex", "manuscript.md"):
        assert "six predefined baselines" in _read(name)


def test_cot_cost_ratio_wording():
    for name in ("main.tex", "manuscript.md"):
        assert "8.3" in _read(name)


def test_b4_downgrade():
    assert "causal prioritization" in _read("main.tex")


def test_section_order():
    tex = _read("main.tex")
    assert (tex.index("\\section{Reproducibility and Ethics}")
            < tex.index("\\section{Limitations}")
            < tex.index("\\bibliography{references}"))
    md = _read("manuscript.md")
    assert (md.index("## 8. Reproducibility and Ethics")
            < md.index("## 9. Limitations") < md.index("## References"))


def test_statistical_language_keeps_effect_sizes():
    tex = _read("main.tex")
    # every "no statistically detectable" claim must coexist with effect
    # sizes and CIs in the document (spot anchors)
    for anchor in ("+1.0$pp", "[-6.00, +3.33]", "[-5.33, +5.33]"):
        assert anchor in tex
