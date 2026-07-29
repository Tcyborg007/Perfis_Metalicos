"""Envelope rastreável de respostas para uma coleção de combinações."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from perfis_metalicos.analysis.beam_fem import (
    BeamAnalysisResult,
    analyze_prismatic_beam,
)
from perfis_metalicos.combinations.generator import LoadCombination
from perfis_metalicos.domain.models import BeamModel
from perfis_metalicos.domain.units import Length, SecondMomentOfArea, Stress


@dataclass(frozen=True, slots=True)
class CombinationAnalysis:
    combination: LoadCombination
    response: BeamAnalysisResult


@dataclass(frozen=True, slots=True)
class EnvelopeExtreme:
    combination_id: str
    value: float
    position: Length


@dataclass(frozen=True, slots=True)
class BeamResponseEnvelope:
    analyses: tuple[CombinationAnalysis, ...]
    maximum_moment: EnvelopeExtreme
    minimum_moment: EnvelopeExtreme
    maximum_shear: EnvelopeExtreme
    minimum_shear: EnvelopeExtreme
    maximum_deflection: EnvelopeExtreme
    minimum_deflection: EnvelopeExtreme

    @property
    def absolute_maximum_moment(self) -> EnvelopeExtreme:
        if abs(self.maximum_moment.value) >= abs(self.minimum_moment.value):
            return self.maximum_moment
        return self.minimum_moment

    @property
    def absolute_maximum_shear(self) -> EnvelopeExtreme:
        if abs(self.maximum_shear.value) >= abs(self.minimum_shear.value):
            return self.maximum_shear
        return self.minimum_shear

    @property
    def absolute_maximum_deflection(self) -> EnvelopeExtreme:
        if abs(self.maximum_deflection.value) >= abs(self.minimum_deflection.value):
            return self.maximum_deflection
        return self.minimum_deflection


def _extreme(
    analyses: tuple[CombinationAnalysis, ...],
    attribute: str,
    *,
    maximum: bool,
) -> EnvelopeExtreme:
    candidates = tuple(
        (analysis, getattr(analysis.response, attribute))
        for analysis in analyses
    )
    selected_analysis, selected_extreme = (
        max(candidates, key=lambda candidate: candidate[1].value)
        if maximum
        else min(candidates, key=lambda candidate: candidate[1].value)
    )
    return EnvelopeExtreme(
        combination_id=selected_analysis.combination.combination_id,
        value=selected_extreme.value,
        position=selected_extreme.position,
    )


def analyze_combination_envelope(
    model: BeamModel,
    combinations: Iterable[LoadCombination],
    elastic_modulus: Stress,
    second_moment: SecondMomentOfArea,
    *,
    relative_tolerance: float = 1e-7,
    max_refinements: int = 8,
) -> BeamResponseEnvelope:
    """Analisa cada combinação sem perder sua identidade e monta os extremos."""

    values = tuple(combinations)
    if not values:
        raise ValueError("Ao menos uma combinação é obrigatória para o envelope.")
    combination_ids = tuple(value.combination_id for value in values)
    if len(combination_ids) != len(set(combination_ids)):
        raise ValueError("combination_id deve ser único no envelope.")

    analyses = tuple(
        CombinationAnalysis(
            combination=combination,
            response=analyze_prismatic_beam(
                model,
                combination.loads,
                elastic_modulus,
                second_moment,
                relative_tolerance=relative_tolerance,
                max_refinements=max_refinements,
            ),
        )
        for combination in values
    )
    unconverged = tuple(
        analysis.combination.combination_id
        for analysis in analyses
        if not analysis.response.converged
    )
    if unconverged:
        joined = ", ".join(unconverged)
        raise RuntimeError(
            f"O envelope foi interrompido por falta de convergência: {joined}."
        )

    return BeamResponseEnvelope(
        analyses=analyses,
        maximum_moment=_extreme(analyses, "maximum_moment", maximum=True),
        minimum_moment=_extreme(analyses, "minimum_moment", maximum=False),
        maximum_shear=_extreme(analyses, "maximum_shear", maximum=True),
        minimum_shear=_extreme(analyses, "minimum_shear", maximum=False),
        maximum_deflection=_extreme(
            analyses,
            "maximum_deflection",
            maximum=True,
        ),
        minimum_deflection=_extreme(
            analyses,
            "minimum_deflection",
            maximum=False,
        ),
    )
