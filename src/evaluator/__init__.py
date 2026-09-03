"""Evaluation package: benchmarks and metrics."""

from .benchmark import get_evaluator, register_benchmark, BENCHMARKS
from .metrics import compute_metrics

__all__ = ["get_evaluator", "register_benchmark", "BENCHMARKS", "compute_metrics"]
