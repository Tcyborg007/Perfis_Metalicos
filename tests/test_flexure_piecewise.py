import math
import re

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
    ("slenderness", "expected_nominal", "expected_design", "regime"),
    (
        (5.0, 100.0, 100.0 / 1.10, FlexuralRegime.PLASTIC_OR_YIELD),
        (15.0, 90.0, 90.0 / 1.10, FlexuralRegime.INELASTIC),
        (25.0, 51.2, 51.2 / 1.10, FlexuralRegime.ELASTIC),
    ),
)
def test_piecewise_returns_exact_strength_and_traceable_inputs(
    slenderness,
    expected_nominal,
    expected_design,
    regime,
):
    result = strength(slenderness)
    assert result.slenderness == slenderness
    assert result.lambda_p == 10.0
    assert result.lambda_r == 20.0
    assert result.nominal_moment.kN_cm == pytest.approx(expected_nominal)
    assert result.design_moment.kN_cm == pytest.approx(expected_design)
    assert result.regime is regime
    assert result.reference is ANNEX_D_D21


def test_piecewise_applies_gamma_once_after_selecting_nominal_strength():
    result = piecewise_design_strength(
        slenderness=15.0,
        lambda_p=10.0,
        lambda_r=20.0,
        plastic_or_yield_moment=Moment(100.0),
        residual_moment=Moment(80.0),
        elastic_critical_moment=Moment(70.0),
        gamma_a1=2.0,
        reference=ANNEX_D_D21,
    )
    assert result.nominal_moment.kN_cm == 90.0
    assert result.design_moment.kN_cm == 45.0


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
    ("lambda_lt", "expected", "regime"),
    (
        (0.2, 1.0, FlexuralRegime.PLASTIC_OR_YIELD),
        (0.9, 0.755, FlexuralRegime.INELASTIC),
        (2.0, 0.25, FlexuralRegime.ELASTIC),
    ),
)
def test_ltb_alternative_exact_values(lambda_lt, expected, regime):
    reduction, actual_regime = ltb_alternative_reduction(lambda_lt)
    assert reduction == pytest.approx(expected)
    assert actual_regime is regime


@pytest.mark.parametrize(
    "invalid",
    (0.0, -1.0, math.inf, math.nan),
)
def test_piecewise_rejects_invalid_slenderness(invalid):
    with pytest.raises(
        ValueError,
        match=re.escape("λ deve ser positivo e finito."),
    ):
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


@pytest.mark.parametrize(
    ("field", "invalid", "label"),
    (
        ("lambda_p", 0.0, "λp"),
        ("lambda_p", math.inf, "λp"),
        ("lambda_r", -1.0, "λr"),
        ("lambda_r", math.nan, "λr"),
        ("gamma_a1", 0.0, "γa1"),
        ("gamma_a1", -1.0, "γa1"),
        ("plastic", 0.0, "Momento de plastificação ou escoamento"),
        ("plastic", -1.0, "Momento de plastificação ou escoamento"),
        ("residual", 0.0, "Momento correspondente ao início do escoamento"),
        ("residual", -1.0, "Momento correspondente ao início do escoamento"),
        ("critical", 0.0, "Momento crítico elástico"),
        ("critical", -1.0, "Momento crítico elástico"),
    ),
)
def test_piecewise_rejects_every_invalid_positive_finite_input(
    field,
    invalid,
    label,
):
    values = {
        "lambda_p": 10.0,
        "lambda_r": 20.0,
        "gamma_a1": 1.10,
        "plastic": 100.0,
        "residual": 80.0,
        "critical": 70.0,
    }
    values[field] = invalid
    with pytest.raises(
        ValueError,
        match=re.escape(f"{label} deve ser positivo e finito."),
    ):
        piecewise_design_strength(
            slenderness=15.0,
            lambda_p=values["lambda_p"],
            lambda_r=values["lambda_r"],
            plastic_or_yield_moment=Moment(values["plastic"]),
            residual_moment=Moment(values["residual"]),
            elastic_critical_moment=Moment(values["critical"]),
            gamma_a1=values["gamma_a1"],
            reference=ANNEX_D_D21,
        )


@pytest.mark.parametrize(
    ("lambda_p", "lambda_r"),
    ((10.0, 10.0), (11.0, 10.0)),
)
def test_piecewise_rejects_non_increasing_slenderness_limits(lambda_p, lambda_r):
    with pytest.raises(
        ValueError,
        match=rf"^{re.escape('λr deve ser maior que λp.')}$",
    ):
        piecewise_design_strength(
            slenderness=10.0,
            lambda_p=lambda_p,
            lambda_r=lambda_r,
            plastic_or_yield_moment=Moment(100.0),
            residual_moment=Moment(80.0),
            elastic_critical_moment=Moment(70.0),
            gamma_a1=1.10,
            reference=ANNEX_D_D21,
        )


def test_piecewise_rejects_residual_moment_above_upper_moment():
    with pytest.raises(
        ValueError,
        match=rf"^{re.escape('O momento residual não pode superar o momento superior.')}$",
    ):
        piecewise_design_strength(
            slenderness=15.0,
            lambda_p=10.0,
            lambda_r=20.0,
            plastic_or_yield_moment=Moment(100.0),
            residual_moment=Moment(100.01),
            elastic_critical_moment=Moment(70.0),
            gamma_a1=1.10,
            reference=ANNEX_D_D21,
        )


def test_piecewise_accepts_residual_moment_equal_to_upper_moment():
    result = piecewise_design_strength(
        slenderness=15.0,
        lambda_p=10.0,
        lambda_r=20.0,
        plastic_or_yield_moment=Moment(100.0),
        residual_moment=Moment(100.0),
        elastic_critical_moment=Moment(70.0),
        gamma_a1=1.10,
        reference=ANNEX_D_D21,
    )
    assert result.nominal_moment.kN_cm == 100.0
    assert result.regime is FlexuralRegime.INELASTIC


@pytest.mark.parametrize("invalid", (0.0, -1.0, math.inf, math.nan))
def test_ltb_alternative_rejects_invalid_slenderness(invalid):
    with pytest.raises(
        ValueError,
        match=re.escape("λLT deve ser positivo e finito."),
    ):
        ltb_alternative_reduction(invalid)
