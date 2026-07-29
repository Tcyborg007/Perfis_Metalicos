"""Matriz de aplicabilidade para forças transversais localizadas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from perfis_metalicos.domain.status import NormativeReference
from perfis_metalicos.domain.units import Force, Length, Stress


class LocalizedForceCase(Enum):
    TENSION_ON_WEB = "TENSION_ON_WEB"
    COMPRESSION_ON_WEB = "COMPRESSION_ON_WEB"
    OPPOSING_COMPRESSION_PAIR = "OPPOSING_COMPRESSION_PAIR"
    PANEL_ZONE = "PANEL_ZONE"
    UNCLASSIFIED = "UNCLASSIFIED"


class LocalizedLimitState(Enum):
    FLANGE_LOCAL_BENDING = "FLANGE_LOCAL_BENDING"
    WEB_LOCAL_YIELDING = "WEB_LOCAL_YIELDING"
    WEB_CRIPPLING = "WEB_CRIPPLING"
    WEB_LATERAL_BUCKLING = "WEB_LATERAL_BUCKLING"
    WEB_COMPRESSION_BUCKLING = "WEB_COMPRESSION_BUCKLING"
    WEB_PANEL_SHEAR = "WEB_PANEL_SHEAR"
    WELD_FORCE_TRANSFER = "WELD_FORCE_TRANSFER"
    STIFFENER_DESIGN = "STIFFENER_DESIGN"
    SUPPORT_END_DETAILING = "SUPPORT_END_DETAILING"


class LimitStateApplicability(Enum):
    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    REQUIRES_CLASSIFICATION = "REQUIRES_CLASSIFICATION"


@dataclass(frozen=True, slots=True)
class LocalizedLimitStateRequirement:
    limit_state: LocalizedLimitState
    applicability: LimitStateApplicability
    reference_item: str
    reason: str


def localized_force_limit_state_matrix(
    case: LocalizedForceCase,
    *,
    welded_section: bool,
    is_support_or_free_end: bool,
) -> tuple[LocalizedLimitStateRequirement, ...]:
    """Retorna a matriz de estados-limite sem converter aplicabilidade em aprovação."""

    requirements: list[LocalizedLimitStateRequirement] = []
    if case is LocalizedForceCase.UNCLASSIFIED:
        return tuple(
            LocalizedLimitStateRequirement(
                limit_state=state,
                applicability=LimitStateApplicability.REQUIRES_CLASSIFICATION,
                reference_item="ABNT NBR 8800:2024, 5.7.1",
                reason="O sentido, a face de aplicação e o tipo da força não foram classificados.",
            )
            for state in LocalizedLimitState
        )

    applicability_by_case = {
        LocalizedForceCase.TENSION_ON_WEB: {
            LocalizedLimitState.FLANGE_LOCAL_BENDING: LimitStateApplicability.CONDITIONAL,
            LocalizedLimitState.WEB_LOCAL_YIELDING: LimitStateApplicability.REQUIRED,
        },
        LocalizedForceCase.COMPRESSION_ON_WEB: {
            LocalizedLimitState.WEB_LOCAL_YIELDING: LimitStateApplicability.REQUIRED,
            LocalizedLimitState.WEB_CRIPPLING: LimitStateApplicability.REQUIRED,
            LocalizedLimitState.WEB_LATERAL_BUCKLING: LimitStateApplicability.CONDITIONAL,
        },
        LocalizedForceCase.OPPOSING_COMPRESSION_PAIR: {
            LocalizedLimitState.WEB_LOCAL_YIELDING: LimitStateApplicability.REQUIRED,
            LocalizedLimitState.WEB_CRIPPLING: LimitStateApplicability.REQUIRED,
            LocalizedLimitState.WEB_COMPRESSION_BUCKLING: LimitStateApplicability.REQUIRED,
        },
        LocalizedForceCase.PANEL_ZONE: {
            LocalizedLimitState.WEB_PANEL_SHEAR: LimitStateApplicability.OUT_OF_SCOPE,
        },
    }
    references = {
        LocalizedLimitState.FLANGE_LOCAL_BENDING: "5.7.2",
        LocalizedLimitState.WEB_LOCAL_YIELDING: "5.7.3",
        LocalizedLimitState.WEB_CRIPPLING: "5.7.4",
        LocalizedLimitState.WEB_LATERAL_BUCKLING: "5.7.5",
        LocalizedLimitState.WEB_COMPRESSION_BUCKLING: "5.7.6",
        LocalizedLimitState.WEB_PANEL_SHEAR: "5.7.7",
        LocalizedLimitState.WELD_FORCE_TRANSFER: "5.7.1 e 5.4.5",
        LocalizedLimitState.STIFFENER_DESIGN: "5.7.9",
        LocalizedLimitState.SUPPORT_END_DETAILING: "5.7.8",
    }
    selected = applicability_by_case[case]
    for state in LocalizedLimitState:
        if state is LocalizedLimitState.WELD_FORCE_TRANSFER:
            applicability = (
                LimitStateApplicability.REQUIRED
                if welded_section
                else LimitStateApplicability.NOT_APPLICABLE
            )
        elif state is LocalizedLimitState.STIFFENER_DESIGN:
            applicability = LimitStateApplicability.CONDITIONAL
        elif state is LocalizedLimitState.SUPPORT_END_DETAILING:
            applicability = (
                LimitStateApplicability.CONDITIONAL
                if is_support_or_free_end
                else LimitStateApplicability.NOT_APPLICABLE
            )
        else:
            applicability = selected.get(
                state,
                LimitStateApplicability.NOT_APPLICABLE,
            )
        requirements.append(
            LocalizedLimitStateRequirement(
                limit_state=state,
                applicability=applicability,
                reference_item=f"ABNT NBR 8800:2024, {references[state]}",
                reason=(
                    f"Aplicabilidade classificada para {case.value}; o cálculo "
                    "da resistência continua sendo uma etapa separada."
                ),
            )
        )
    return tuple(requirements)


FLANGE_LOCAL_BENDING_REFERENCE = NormativeReference(
    standard="ABNT NBR 8800",
    edition="2024",
    item="5.7.2.1 a 5.7.2.4",
    page=64,
    review_status="SOURCE_VISUALLY_VERIFIED",
)


def flange_local_bending_resistance(
    *,
    flange_thickness: Length,
    yield_strength: Stress,
    distance_to_end: Length,
    transverse_load_length: Length,
    flange_width: Length,
    gamma_a1: float,
) -> Force | None:
    """Resistência de 5.7.2; ``None`` comprova a não aplicabilidade de 5.7.2.1."""

    flange_thickness.require_positive("tf")
    yield_strength.require_positive("fy")
    flange_width.require_positive("bf")
    if distance_to_end.cm < 0:
        raise ValueError("A distância à extremidade não pode ser negativa.")
    transverse_load_length.require_positive("Comprimento transversal da força")
    if gamma_a1 <= 0:
        raise ValueError("γa1 deve ser positivo.")
    if transverse_load_length.cm < 0.15 * flange_width.cm:
        return None
    resistance = (
        6.25
        * flange_thickness.cm**2
        * yield_strength.kN_per_cm2
        / gamma_a1
    )
    if distance_to_end.cm < 10.0 * flange_thickness.cm:
        resistance *= 0.5
    return Force(resistance)

