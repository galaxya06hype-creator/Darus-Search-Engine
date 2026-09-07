"""
Source-quality scoring: the invisible trust signal.

This module turns a list of raw search results into results annotated
with a `quality` block that captures *why* a reader should or should
not weight a given source. The four signals we compute are deliberately
rule-based -- LLM judgments are subjective and opaque; these are
auditable and reproducible across runs.

See score.py for the scoring logic and ``assess_results`` for the
batch API used by the tools.
"""

from .score import (
    DomainTier,
    QualityScore,
    assess_results,
    score_url,
    summarize_quality,
)

__all__ = [
    "DomainTier",
    "QualityScore",
    "assess_results",
    "score_url",
    "summarize_quality",
]
