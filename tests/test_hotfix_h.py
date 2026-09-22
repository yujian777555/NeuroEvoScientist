"""Phase-20 hotfix gate tests (H1-H6)."""

import json
import os
import subprocess
import sys

import pytest

from genome.structured import StructuredGenome
from genome.structured_space import StructuredSearchSpace
from evaluator.memory import hashed_embedding
from evaluator.prompts import reasoning_prompt
from evaluator.qasper import _longbench_normalize, qa_f1

SRC = os.path.join(os.path.dirname(__file__), "..", "src")


def test_h1_embeddings_stable_across_processes():
    """H1: identical embeddings in two independent Python processes."""
    code = (
        "import sys; sys.path.insert(0, {p!r}); "
        "from evaluator.memory import hashed_embedding; "
        "v = hashed_embedding('the cat sat', 16); "
        "print(','.join(format(float(x), '.6f') for x in v.tolist()))"
    ).format(p=os.path.abspath(SRC))
    cmd = [sys.executable, "-c", code]
    out1 = subprocess.check_output(cmd, text=True).strip()
    out2 = subprocess.check_output(cmd, text=True).strip()
    assert out1 == out2
    assert out1 != ",".join(["0.000000"] * 16)


def test_h2_no_memory_phenotypes_dedup():
    """H2: exemplar_count=0 collapses all memory variants to one phenotype."""
    hashes = set()
    for mt in ("recency", "retrieval", "mamba2", "hybrid"):
        g = StructuredGenome(memory_type=mt, exemplar_count=0,
                             mamba_state_size=256, hybrid_fraction=0.5,
                             retrieval_metric="hashed_bow",
                             adaptation_enabled=True, adaptation_steps=20)
        hashes.add(g.phenotype_hash())
    assert len(hashes) == 1
    g = StructuredGenome(exemplar_count=0)
    assert g.normalize().memory_type == "none"
    assert g.normalize().adaptation_enabled is False


def test_h3_verifier_passes_exact():
    """H3: every verifier_passes value maps to exactly N passes."""
    for n in (1, 2, 3):
        g = StructuredGenome(reasoning="verify", verifier_passes=n)
        prompt = reasoning_prompt(g, "Q?", "HINT")
        assert "%d times" % n in prompt
        if n != 1:
            assert "1 times" not in prompt
    # 0 is no longer in the search space
    space = StructuredSearchSpace()
    assert 0 not in space.reasoning["verifier_passes"]


def test_h5_honest_retrieval_naming():
    """H5: no 'dense' anywhere in space/controller; hashed_bow present."""
    space = StructuredSearchSpace()
    assert "hashed_bow" in space.memory["retrieval_metric"]
    assert "dense" not in space.memory["retrieval_metric"]
    from evaluator.memory import RetrievalMemoryController
    ctrl = RetrievalMemoryController(
        StructuredGenome(memory_type="retrieval",
                         retrieval_metric="hashed_bow"))
    assert ctrl.metric == "hashed_bow"


def test_h6_longbench_normalization():
    """H6: LongBench-compatible normalization (case/punct/articles/space)."""
    assert _longbench_normalize("The Quick, Brown FOX!") == "quick brown fox"
    assert _longbench_normalize("An  apple   a  day") == "apple day"
    # "is" is not an article: overlap 2/3 -> F1 = 0.8
    assert qa_f1("the answer is 42!", "answer 42") == pytest.approx(0.8)
    assert qa_f1("A bag of apples", "bag of apples") == pytest.approx(1.0)


def test_cache_version_bumped():
    """Cache isolation: pipeline key bumped so pre/post-hotfix never mix."""
    import io
    for path in ("evaluator/gsm8k.py", "evaluator/pubmedqa.py",
                 "evaluator/qasper.py"):
        src = io.open(os.path.join(SRC, *path.split("/")),
                      encoding="utf-8").read()
        assert '"pipeline": "phase20-v4"' in src
        assert '"pipeline": "phase17-v3"' not in src


def test_input_context_budget_reaches_prompt():
    """H4: genome input_context_budget changes document words in the prompt."""
    from evaluator.qasper import QasperEvaluator
    words = " ".join("w%d" % i for i in range(3000))
    sample = {"context": words, "input": "Q?", "answers": ["x"]}
    ev = QasperEvaluator(backend=lambda p, g: "")
    g = StructuredGenome(input_context_budget=512)
    ctx, _ = ev._render_sample(sample, g)
    assert len(ctx.split()) == 512
    ctx2, _ = ev._render_sample(sample, None)  # legacy fallback
    assert len(ctx2.split()) == 2500
