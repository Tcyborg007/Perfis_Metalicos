import pytest

from perfis_metalicos.analysis import analyze_prismatic_beam
from perfis_metalicos.domain import (
    AppliedMoment,
    BeamModel,
    ConcentratedLoad,
    Force,
    Length,
    LinearlyVaryingLoad,
    LineLoad,
    Moment,
    SecondMomentOfArea,
    Stress,
    SupportCondition,
    UniformLineLoad,
)


E = Stress(20_000.0)
I = SecondMomentOfArea(10_000.0)
L = 500.0


def model(support: SupportCondition) -> BeamModel:
    return BeamModel(Length(L), support)


def test_simply_supported_uniform_load_matches_closed_form():
    q = 0.1
    result = analyze_prismatic_beam(
        model(SupportCondition.SIMPLY_SUPPORTED),
        (UniformLineLoad(Length(0), Length(L), LineLoad(q)),),
        E,
        I,
    )
    expected_m = q * L**2 / 8.0
    expected_d = 5.0 * q * L**4 / (384.0 * E.kN_per_cm2 * I.cm4)

    assert result.converged
    assert result.reaction_left.kN == pytest.approx(q * L / 2.0, rel=1e-8)
    assert result.reaction_right.kN == pytest.approx(q * L / 2.0, rel=1e-8)
    assert result.maximum_moment.value == pytest.approx(expected_m, rel=1e-8)
    assert result.maximum_moment.position.cm == pytest.approx(L / 2.0)
    assert result.maximum_deflection.value == pytest.approx(expected_d, rel=1e-7)
    assert result.maximum_deflection.position.cm == pytest.approx(L / 2.0)
    assert abs(result.rotation_at(result.maximum_deflection.position.cm)) < 1e-10


def test_partial_uniform_load_has_exact_equilibrium_reactions():
    q = 0.08
    start, end = 100.0, 300.0
    total = q * (end - start)
    centroid = (start + end) / 2.0
    expected_right = total * centroid / L
    expected_left = total - expected_right
    result = analyze_prismatic_beam(
        model(SupportCondition.SIMPLY_SUPPORTED),
        (UniformLineLoad(Length(start), Length(end), LineLoad(q)),),
        E,
        I,
    )
    assert result.reaction_left.kN == pytest.approx(expected_left, rel=1e-8)
    assert result.reaction_right.kN == pytest.approx(expected_right, rel=1e-8)
    assert result.shear_at(L, after_point=True) == pytest.approx(-expected_right)


def test_multiple_point_loads_and_moment_are_combined_in_one_model():
    loads = (
        ConcentratedLoad(Length(100), Force(10)),
        ConcentratedLoad(Length(350), Force(20)),
        AppliedMoment(Length(250), Moment(500)),
    )
    result = analyze_prismatic_beam(
        model(SupportCondition.SIMPLY_SUPPORTED),
        loads,
        E,
        I,
    )
    assert result.reaction_left.kN + result.reaction_right.kN == pytest.approx(30.0)
    assert result.moment_at(250, after_moment=False) - result.moment_at(
        250, after_moment=True
    ) == pytest.approx(500.0)
    assert abs(result.rotation_at(result.maximum_deflection.position.cm)) < 1e-9


def test_linearly_varying_load_reactions_match_resultant_and_centroid():
    q_end = 0.12
    total = q_end * L / 2.0
    centroid = 2.0 * L / 3.0
    expected_right = total * centroid / L
    result = analyze_prismatic_beam(
        model(SupportCondition.SIMPLY_SUPPORTED),
        (
            LinearlyVaryingLoad(
                Length(0),
                Length(L),
                LineLoad(0),
                LineLoad(q_end),
            ),
        ),
        E,
        I,
    )
    assert result.reaction_right.kN == pytest.approx(expected_right, rel=1e-8)
    assert result.reaction_left.kN == pytest.approx(total - expected_right, rel=1e-8)


def test_fixed_fixed_uniform_load_matches_end_moments_and_midspan_deflection():
    q = 0.1
    result = analyze_prismatic_beam(
        model(SupportCondition.FIXED_FIXED),
        (UniformLineLoad(Length(0), Length(L), LineLoad(q)),),
        E,
        I,
    )
    expected_end = -q * L**2 / 12.0
    expected_d = q * L**4 / (384.0 * E.kN_per_cm2 * I.cm4)
    assert result.moment_left.kN_cm == pytest.approx(expected_end, rel=1e-9)
    assert result.moment_right.kN_cm == pytest.approx(expected_end, rel=1e-9)
    assert result.maximum_deflection.value == pytest.approx(expected_d, rel=1e-7)
    assert result.maximum_deflection.position.cm == pytest.approx(L / 2.0)


def test_cantilever_uniform_load_matches_closed_form():
    q = 0.1
    result = analyze_prismatic_beam(
        model(SupportCondition.CANTILEVER),
        (UniformLineLoad(Length(0), Length(L), LineLoad(q)),),
        E,
        I,
    )
    expected_d = q * L**4 / (8.0 * E.kN_per_cm2 * I.cm4)
    assert result.reaction_left.kN == pytest.approx(q * L, rel=1e-8)
    assert result.reaction_right.kN == pytest.approx(0.0, abs=1e-8)
    assert result.moment_left.kN_cm == pytest.approx(-q * L**2 / 2.0, rel=1e-8)
    assert result.moment_right.kN_cm == pytest.approx(0.0, abs=1e-8)
    assert result.maximum_deflection.value == pytest.approx(expected_d, rel=1e-7)
    assert result.maximum_deflection.position.cm == pytest.approx(L)


def test_propped_cantilever_uniform_load_matches_compatibility_solution():
    q = 0.1
    result = analyze_prismatic_beam(
        model(SupportCondition.PROPPED_CANTILEVER),
        (UniformLineLoad(Length(0), Length(L), LineLoad(q)),),
        E,
        I,
    )
    assert result.reaction_left.kN == pytest.approx(5.0 * q * L / 8.0, rel=1e-8)
    assert result.reaction_right.kN == pytest.approx(3.0 * q * L / 8.0, rel=1e-8)
    assert result.moment_left.kN_cm == pytest.approx(-q * L**2 / 8.0, rel=1e-8)
    assert result.moment_right.kN_cm == pytest.approx(0.0, abs=1e-8)
    assert result.displacement_at(L) == pytest.approx(0.0, abs=1e-10)


def test_load_outside_span_is_rejected():
    with pytest.raises(ValueError, match="fora do vão"):
        analyze_prismatic_beam(
            model(SupportCondition.SIMPLY_SUPPORTED),
            (ConcentratedLoad(Length(L + 1), Force(10)),),
            E,
            I,
        )


def test_nonconvergence_is_reported_instead_of_hidden():
    result = analyze_prismatic_beam(
        model(SupportCondition.SIMPLY_SUPPORTED),
        (UniformLineLoad(Length(0), Length(L), LineLoad(0.1)),),
        E,
        I,
        relative_tolerance=1e-16,
        max_refinements=2,
    )
    assert not result.converged
    assert result.estimated_relative_error > result.requested_relative_tolerance
