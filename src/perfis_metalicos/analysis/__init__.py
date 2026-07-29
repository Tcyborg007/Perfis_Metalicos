"""Análise estrutural independente da interface."""

from perfis_metalicos.analysis.beam_fem import (
    BeamAnalysisResult,
    BeamExtremum,
    analyze_prismatic_beam,
)

__all__ = ["BeamAnalysisResult", "BeamExtremum", "analyze_prismatic_beam"]

