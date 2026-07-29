"""Análise estrutural independente da interface."""

from perfis_metalicos.analysis.beam_fem import (
    BeamAnalysisResult,
    BeamExtremum,
    analyze_prismatic_beam,
)
from perfis_metalicos.analysis.stability_segments import (
    ContinuousFlangeRestraint,
    Flange,
    LoadApplicationHeight,
    RestraintPoint,
    SegmentFltCheck,
    SegmentMomentData,
    UnbracedSegment,
    build_unbraced_segments,
    evaluate_flt_segments,
    governing_flt_segment,
    segment_moment_data,
)

__all__ = [
    "BeamAnalysisResult",
    "BeamExtremum",
    "ContinuousFlangeRestraint",
    "Flange",
    "LoadApplicationHeight",
    "RestraintPoint",
    "SegmentFltCheck",
    "SegmentMomentData",
    "UnbracedSegment",
    "analyze_prismatic_beam",
    "build_unbraced_segments",
    "evaluate_flt_segments",
    "governing_flt_segment",
    "segment_moment_data",
]

