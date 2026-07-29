"""Primitivas normativas centralizadas para resistência à flexão.

Este módulo contém apenas regras já conferidas na cópia controlada da
ABNT NBR 8800:2024. A eventual influência da Errata 1:2025 permanece marcada
no manifesto como ``NORMATIVE_REVIEW_REQUIRED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from perfis_metalicos.domain.status import NormativeReference
from perfis_metalicos.domain.units import Moment

ANNEX_D_D21 = NormativeReference(
    standard="ABNT NBR 8800",
    edition="2024",
    item="D.2.1",
    page=137,
    review_status="SOURCE_VISUALLY_VERIFIED",
)
ANNEX_D_D22 = NormativeReference(
    standard="ABNT NBR 8800",
    edition="2024",
    item="D.2.2",
    page=138,
    review_status="SOURCE_VISUALLY_VERIFIED",
)


class FlexuralRegime(Enum):
    PLASTIC_OR_YIELD = "PLASTIC_OR_YIELD"
    INELASTIC = "INELASTIC"
    ELASTIC = "ELASTIC"


@dataclass(frozen=True, slots=True)
class PiecewiseStrengthResult:
    slenderness: float
    lambda_p: float
    lambda_r: float
    nominal_moment: Moment
    design_moment: Moment
    regime: FlexuralRegime
    reference: NormativeReference


def _positive_finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} deve ser positivo e finito.")
    return number


def piecewise_design_strength(
    *,
    slenderness: float,
    lambda_p: float,
    lambda_r: float,
    plastic_or_yield_moment: Moment,
    residual_moment: Moment,
    elastic_critical_moment: Moment,
    gamma_a1: float,
    reference: NormativeReference,
) -> PiecewiseStrengthResult:
    """Aplica a função por partes comum a D.2.1 e D.2.2.

    Os momentos de entrada são nominais. O coeficiente ``gamma_a1`` é aplicado
    uma única vez, depois da seleção do regime.
    """

    slenderness = _positive_finite(slenderness, "λ")
    lambda_p = _positive_finite(lambda_p, "λp")
    lambda_r = _positive_finite(lambda_r, "λr")
    gamma_a1 = _positive_finite(gamma_a1, "γa1")
    if lambda_r <= lambda_p:
        raise ValueError("λr deve ser maior que λp.")
    plastic = _positive_finite(
        plastic_or_yield_moment.kN_cm,
        "Momento de plastificação ou escoamento",
    )
    residual = _positive_finite(
        residual_moment.kN_cm,
        "Momento correspondente ao início do escoamento",
    )
    critical = _positive_finite(
        elastic_critical_moment.kN_cm,
        "Momento crítico elástico",
    )
    if residual > plastic:
        raise ValueError("O momento residual não pode superar o momento superior.")

    if slenderness <= lambda_p:
        nominal = plastic
        regime = FlexuralRegime.PLASTIC_OR_YIELD
    elif slenderness <= lambda_r:
        interpolation = (slenderness - lambda_p) / (lambda_r - lambda_p)
        nominal = plastic - (plastic - residual) * interpolation
        regime = FlexuralRegime.INELASTIC
    else:
        nominal = critical
        regime = FlexuralRegime.ELASTIC

    return PiecewiseStrengthResult(
        slenderness=slenderness,
        lambda_p=lambda_p,
        lambda_r=lambda_r,
        nominal_moment=Moment(nominal),
        design_moment=Moment(nominal / gamma_a1),
        regime=regime,
        reference=reference,
    )


def ltb_alternative_reduction(lambda_lt: float) -> tuple[float, FlexuralRegime]:
    """Coeficiente χLT do procedimento alternativo de D.2.1."""

    lambda_lt = _positive_finite(lambda_lt, "λLT")
    if lambda_lt <= 0.4:
        return 1.0, FlexuralRegime.PLASTIC_OR_YIELD
    if lambda_lt <= 1.4:
        return 1.0 - 0.49 * (lambda_lt - 0.4), FlexuralRegime.INELASTIC
    return 1.0 / lambda_lt**2, FlexuralRegime.ELASTIC

