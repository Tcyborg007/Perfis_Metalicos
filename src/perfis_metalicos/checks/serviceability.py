"""Modelo auditável de parcelas e fases para deslocamentos em serviço."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from perfis_metalicos.domain.status import (
    NormativeReference,
    VerificationResult,
    VerificationStatus,
)
from perfis_metalicos.domain.units import Length
from perfis_metalicos.version import ENGINE_VERSION


class ServiceCombinationFamily(Enum):
    RARE = "RARE"
    FREQUENT = "FREQUENT"
    QUASI_PERMANENT = "QUASI_PERMANENT"


class DeflectionCriterion(Enum):
    TOTAL = "TOTAL"
    AFTER_FRAGILE_ELEMENT = "AFTER_FRAGILE_ELEMENT"
    VARIABLE_COMPONENT = "VARIABLE_COMPONENT"
    RELATIVE_BETWEEN_POINTS = "RELATIVE_BETWEEN_POINTS"


@dataclass(frozen=True, slots=True)
class ConstructionPhaseDeflection:
    phase_id: str
    permanent_before_fragile: Length
    permanent_after_fragile: Length
    leading_variable: Length
    accompanying_variables: Length
    relative_between_points: Length | None = None

    def __post_init__(self) -> None:
        if not self.phase_id.strip():
            raise ValueError("A fase construtiva deve possuir identificação.")

    @property
    def total_before_camber(self) -> Length:
        return Length(
            self.permanent_before_fragile.cm
            + self.permanent_after_fragile.cm
            + self.leading_variable.cm
            + self.accompanying_variables.cm
        )


@dataclass(frozen=True, slots=True)
class ServiceabilityLimit:
    criterion: DeflectionCriterion
    limit: Length
    sensitive_element: str
    reference: NormativeReference

    def __post_init__(self) -> None:
        self.limit.require_positive("Limite de deslocamento")
        if not self.sensitive_element.strip():
            raise ValueError("O elemento sensível associado é obrigatório.")


def _criterion_demand(
    phase: ConstructionPhaseDeflection,
    criterion: DeflectionCriterion,
    camber: Length,
) -> float:
    if camber.cm < 0:
        raise ValueError("A contraflecha não pode ser negativa.")
    if criterion is DeflectionCriterion.TOTAL:
        return max(abs(phase.total_before_camber.cm) - camber.cm, 0.0)
    if criterion is DeflectionCriterion.AFTER_FRAGILE_ELEMENT:
        return abs(
            phase.permanent_after_fragile.cm
            + phase.leading_variable.cm
            + phase.accompanying_variables.cm
        )
    if criterion is DeflectionCriterion.VARIABLE_COMPONENT:
        return abs(
            phase.leading_variable.cm + phase.accompanying_variables.cm
        )
    if phase.relative_between_points is None:
        raise ValueError("O deslocamento relativo entre pontos não foi informado.")
    return abs(phase.relative_between_points.cm)


def evaluate_serviceability_deflection(
    *,
    check_id: str,
    phase: ConstructionPhaseDeflection,
    combination: ServiceCombinationFamily,
    limit: ServiceabilityLimit,
    camber: Length | None = None,
    position: Length | None = None,
    engine_version: str = ENGINE_VERSION,
) -> VerificationResult:
    camber = camber or Length(0.0)
    demand = _criterion_demand(phase, limit.criterion, camber)
    utilization = demand / limit.limit.cm
    reviewed = limit.reference.review_status not in {
        "NORMATIVE_REVIEW_REQUIRED",
        "UNREVIEWED",
    }
    if not reviewed:
        status = VerificationStatus.NOT_CHECKED
        justification = (
            "A parcela foi calculada, mas a origem normativa do limite ainda "
            "requer revisão controlada."
        )
    else:
        status = (
            VerificationStatus.PASS
            if utilization <= 1.0
            else VerificationStatus.FAIL
        )
        justification = (
            "Parcela de deslocamento comparada ao limite da fase e do elemento "
            "sensível declarados."
        )
    return VerificationResult(
        check_id=check_id,
        demand=Length(demand),
        resistance_or_limit=limit.limit,
        utilization=utilization,
        status=status,
        justification=justification,
        normative_references=(limit.reference,),
        assumptions=(
            f"Critério: {limit.criterion.value}.",
            f"Elemento sensível: {limit.sensitive_element}.",
            f"Contraflecha informada: {camber.cm} cm.",
        ),
        combination=combination.value,
        position=position,
        engine_version=engine_version,
        metadata={
            "phase": phase.phase_id,
            "permanent_before_fragile_cm": phase.permanent_before_fragile.cm,
            "permanent_after_fragile_cm": phase.permanent_after_fragile.cm,
            "leading_variable_cm": phase.leading_variable.cm,
            "accompanying_variables_cm": phase.accompanying_variables.cm,
            "camber_cm": camber.cm,
        },
    )


def vibration_out_of_scope_result() -> VerificationResult:
    return VerificationResult(
        check_id="ELS_VIBRATION",
        demand=None,
        resistance_or_limit=None,
        utilization=None,
        status=VerificationStatus.OUT_OF_SCOPE,
        justification=(
            "A análise dinâmica de vibração não foi implementada e não pode ser "
            "substituída pela verificação estática de flecha."
        ),
        normative_references=(
            NormativeReference(
                standard="ABNT NBR 8800",
                edition="2024",
                item="Anexo I",
                review_status="NORMATIVE_REVIEW_REQUIRED",
            ),
        ),
    )
