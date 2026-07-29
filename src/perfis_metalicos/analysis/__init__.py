"""Análise estrutural independente da interface."""

from perfis_metalicos.analysis.beam_fem import (
    BeamAnalysisResult,
    BeamExtremum,
    analyze_prismatic_beam,
)
from perfis_metalicos.analysis.envelope import (
    BeamResponseEnvelope,
    CombinationAnalysis,
    EnvelopeExtreme,
    analyze_combination_envelope,
)
from perfis_metalicos.analysis.stability_segments import (
    ContinuousFlangeCbCase,
    ContinuousFlangeRestraint,
    Flange,
    LoadApplicationHeight,
    RestraintPoint,
    SegmentFltCheck,
    SegmentMomentData,
    UnbracedSegment,
    build_unbraced_segments,
    continuous_flange_cb,
    evaluate_flt_segments,
    governing_flt_segment,
    segment_moment_data,
)

__all__ = [
    "BeamAnalysisResult",
    "BeamExtremum",
    "BeamResponseEnvelope",
    "CombinationAnalysis",
    "ContinuousFlangeCbCase",
    "ContinuousFlangeRestraint",
    "EnvelopeExtreme",
    "Flange",
    "LoadApplicationHeight",
    "RestraintPoint",
    "SegmentFltCheck",
    "SegmentMomentData",
    "UnbracedSegment",
    "analyze_prismatic_beam",
    "analyze_combination_envelope",
    "build_unbraced_segments",
    "continuous_flange_cb",
    "evaluate_flt_segments",
    "governing_flt_segment",
    "segment_moment_data",
]
