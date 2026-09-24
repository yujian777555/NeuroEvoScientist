"""Phase-21 Task 1: task-aware phenotype canonicalization."""

from genome.structured import (StructuredGenome, effective_genome_for_task,
                               task_phenotype_hash)


def test_input_budget_inert_on_short_tasks():
    a = StructuredGenome(input_context_budget=512)
    b = StructuredGenome(input_context_budget=4096)
    for bench in ("gsm8k", "pubmedqa"):
        assert task_phenotype_hash(a, bench) == task_phenotype_hash(b, bench)
        assert effective_genome_for_task(a, bench).input_context_budget is None


def test_input_budget_active_on_qasper():
    a = StructuredGenome(input_context_budget=512)
    b = StructuredGenome(input_context_budget=4096)
    assert task_phenotype_hash(a, "qasper") != task_phenotype_hash(b, "qasper")
    assert effective_genome_for_task(a, "qasper").input_context_budget == 512


def test_other_normalization_still_applies_per_task():
    g = StructuredGenome(memory_type="recency", retrieval_metric="hashed_bow",
                         input_context_budget=1024)
    e = effective_genome_for_task(g, "gsm8k")
    assert e.retrieval_metric is None
    assert e.input_context_budget is None
    e2 = effective_genome_for_task(g, "qasper")
    assert e2.retrieval_metric is None  # recency -> metric inactive anyway


def test_cache_key_dedup_on_gsm8k():
    from evaluator.gsm8k import GSM8KEvaluator
    ev = GSM8KEvaluator(backend=lambda p, g: "")
    a = StructuredGenome(input_context_budget=512)
    b = StructuredGenome(input_context_budget=4096)
    assert ev._cache_key(a) == ev._cache_key(b)


def test_cache_key_distinct_on_qasper():
    from evaluator.qasper import QasperEvaluator
    ev = QasperEvaluator(backend=lambda p, g: "")
    a = StructuredGenome(input_context_budget=512)
    b = StructuredGenome(input_context_budget=4096)
    assert ev._cache_key(a) != ev._cache_key(b)
