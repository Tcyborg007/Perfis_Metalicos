import pytest

from perfis_metalicos.checks import (
    LimitStateApplicability,
    LocalizedForceCase,
    LocalizedLimitState,
    flange_local_bending_resistance,
    localized_force_limit_state_matrix,
)
from perfis_metalicos.domain import Length, Stress


def matrix(case, *, welded=False, support=False):
    return {
        item.limit_state: item.applicability
        for item in localized_force_limit_state_matrix(
            case,
            welded_section=welded,
            is_support_or_free_end=support,
        )
    }


def test_tension_and_compression_have_different_required_limit_states():
    tension = matrix(LocalizedForceCase.TENSION_ON_WEB)
    compression = matrix(LocalizedForceCase.COMPRESSION_ON_WEB)
    assert tension[LocalizedLimitState.FLANGE_LOCAL_BENDING] is LimitStateApplicability.CONDITIONAL
    assert tension[LocalizedLimitState.WEB_CRIPPLING] is LimitStateApplicability.NOT_APPLICABLE
    assert compression[LocalizedLimitState.WEB_CRIPPLING] is LimitStateApplicability.REQUIRED
    assert compression[LocalizedLimitState.FLANGE_LOCAL_BENDING] is LimitStateApplicability.NOT_APPLICABLE


def test_weld_transfer_and_support_detailing_are_not_hidden():
    values = matrix(
        LocalizedForceCase.COMPRESSION_ON_WEB,
        welded=True,
        support=True,
    )
    assert values[LocalizedLimitState.WELD_FORCE_TRANSFER] is LimitStateApplicability.REQUIRED
    assert values[LocalizedLimitState.SUPPORT_END_DETAILING] is LimitStateApplicability.CONDITIONAL
    assert values[LocalizedLimitState.STIFFENER_DESIGN] is LimitStateApplicability.CONDITIONAL


def test_unclassified_force_never_defaults_to_compression():
    requirements = localized_force_limit_state_matrix(
        LocalizedForceCase.UNCLASSIFIED,
        welded_section=True,
        is_support_or_free_end=True,
    )
    assert all(
        item.applicability is LimitStateApplicability.REQUIRES_CLASSIFICATION
        for item in requirements
    )


def test_opposing_pair_requires_web_compression_buckling():
    values = matrix(LocalizedForceCase.OPPOSING_COMPRESSION_PAIR)
    assert values[LocalizedLimitState.WEB_COMPRESSION_BUCKLING] is LimitStateApplicability.REQUIRED


def test_flange_local_bending_not_applicable_below_015_bf():
    resistance = flange_local_bending_resistance(
        flange_thickness=Length(1.0),
        yield_strength=Stress(25.0),
        distance_to_end=Length(20.0),
        transverse_load_length=Length(2.9),
        flange_width=Length(20.0),
        gamma_a1=1.10,
    )
    assert resistance is None


def test_flange_local_bending_and_end_reduction():
    common = dict(
        flange_thickness=Length(1.0),
        yield_strength=Stress(25.0),
        transverse_load_length=Length(3.0),
        flange_width=Length(20.0),
        gamma_a1=1.10,
    )
    internal = flange_local_bending_resistance(
        **common,
        distance_to_end=Length(10.0),
    )
    near_end = flange_local_bending_resistance(
        **common,
        distance_to_end=Length(9.999),
    )
    assert internal is not None
    assert near_end is not None
    assert internal.kN == pytest.approx(6.25 * 1.0**2 * 25.0 / 1.10)
    assert near_end.kN == pytest.approx(0.5 * internal.kN)

