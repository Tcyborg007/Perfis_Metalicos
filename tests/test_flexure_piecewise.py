import math

import pytest

from perfis_metalicos.checks import (
    ANNEX_D_D21,
    FlexuralRegime,
    ltb_alternative_reduction,
    piecewise_design_strength,
)
from perfis_metalicos.domain import Moment

EPSILON = 1e-8


def strength(slenderness: float):
    lambda_p = 10.0
    lambda_r = 20.0
    critical = 80.0 * (lambda_r / slenderness) ** 2
    return piecewise_design_strength(
        slenderness=slenderness,
        lambda_p=lambda_p,
        lambda_r=lambda_r,
        plastic_or_yield_moment=Moment(100.0),
        residual_moment=Moment(80.0),
        elastic_critical_moment=Moment(critical),
        gamma_a1=1.10,
        reference=ANNEX_D_D21,
    )


@pytest.mark.parametrize(
    ("slenderness", "expected_regime"),
    (
        (10.0 - EPSILON, FlexuralRegime.PLASTIC_OR_YIELD),
        (10.0, FlexuralRegime.PLASTIC_OR_YIELD),
        (10.0 + EPSILON, FlexuralRegime.INELASTIC),
        (20.0 - EPSILON, FlexuralRegime.INELASTIC),
        (20.0, FlexuralRegime.INELASTIC),
        (20.0 + EPSILON, FlexuralRegime.ELASTIC),
    ),
)
def test_piecewise_regime_at_both_boundaries(slenderness, expected_regime):
    assert strength(slenderness).regime is expected_regime


def test_piecewise_is_continuous_at_lambda_p_and_lambda_r():
    below_p = strength(10.0 - EPSILON).design_moment.kN_cm
    at_p = strength(10.0).design_moment.kN_cm
    above_p = strength(10.0 + EPSILON).design_moment.kN_cm
    below_r = strength(20.0 - EPSILON).design_moment.kN_cm
    at_r = strength(20.0).design_moment.kN_cm
    above_r = strength(20.0 + EPSILON).design_moment.kN_cm
    assert below_p == pytest.approx(at_p, rel=1e-8)
    assert above_p == pytest.approx(at_p, rel=1e-8)
    assert below_r == pytest.approx(at_r, rel=1e-8)
    assert above_r == pytest.approx(at_r, rel=1e-8)


def test_piecewise_expected_monotonicity():
    values = [strength(value).design_moment.kN_cm for value in (8, 10, 12, 16, 20, 24)]
    assert values == sorted(values, reverse=True)


@pytest.mark.parametrize(
    ("lambda_lt", "regime"),
    (
        (0.4 - EPSILON, FlexuralRegime.PLASTIC_OR_YIELD),
        (0.4, FlexuralRegime.PLASTIC_OR_YIELD),
        (0.4 + EPSILON, FlexuralRegime.INELASTIC),
        (1.4 - EPSILON, FlexuralRegime.INELASTIC),
        (1.4, FlexuralRegime.INELASTIC),
        (1.4 + EPSILON, FlexuralRegime.ELASTIC),
    ),
)
def test_ltb_alternative_regime_boundaries(lambda_lt, regime):
    _, actual = ltb_alternative_reduction(lambda_lt)
    assert actual is regime


def test_ltb_alternative_transition_at_04_is_continuous():
    at, _ = ltb_alternative_reduction(0.4)
    below, _ = ltb_alternative_reduction(0.4 - EPSILON)
    above, _ = ltb_alternative_reduction(0.4 + EPSILON)
    assert below == pytest.approx(at, rel=1e-7)
    assert above == pytest.approx(at, rel=1e-7)


def test_ltb_alternative_transition_at_14_has_only_formula_rounding_jump():
    at, _ = ltb_alternative_reduction(1.4)
    above, _ = ltb_alternative_reduction(1.4 + EPSILON)
    relative_jump = abs(above - at) / at
    assert relative_jump < 5e-4


@pytest.mark.parametrize(
    "invalid",
    (0.0, -1.0, math.inf, math.nan),
)
def test_piecewise_rejects_invalid_slenderness(invalid):
    with pytest.raises(ValueError):
        piecewise_design_strength(
            slenderness=invalid,
            lambda_p=10.0,
            lambda_r=20.0,
            plastic_or_yield_moment=Moment(100.0),
            residual_moment=Moment(80.0),
            elastic_critical_moment=Moment(70.0),
            gamma_a1=1.10,
            reference=ANNEX_D_D21,
        )
