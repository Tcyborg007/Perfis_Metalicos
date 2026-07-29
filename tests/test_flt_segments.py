import pytest

from perfis_metalicos.analysis import (
    ContinuousFlangeCbCase,
    ContinuousFlangeRestraint,
    Flange,
    LoadApplicationHeight,
    RestraintPoint,
    build_unbraced_segments,
    continuous_flange_cb,
    evaluate_flt_segments,
    governing_flt_segment,
    segment_moment_data,
)
from perfis_metalicos.analysis import analyze_prismatic_beam
from perfis_metalicos.domain import (
    BeamModel,
    Length,
    LineLoad,
    Moment,
    SecondMomentOfArea,
    Stress,
    SupportCondition,
    UniformLineLoad,
    VerificationStatus,
)


def response():
    return analyze_prismatic_beam(
        BeamModel(Length(600), SupportCondition.SIMPLY_SUPPORTED),
        (UniformLineLoad(Length(0), Length(600), LineLoad(0.1)),),
        Stress(20_000),
        SecondMomentOfArea(10_000),
    )


def restraint(position: float, name: str) -> RestraintPoint:
    return RestraintPoint(
        position=Length(position),
        top_flange_lateral=True,
        bottom_flange_lateral=True,
        torsional=True,
        warping=False,
        restraint_id=name,
    )


def selective_restraint(
    position: float,
    name: str,
    *,
    top: bool = True,
    bottom: bool = True,
    torsional: bool = True,
    warping: bool = False,
) -> RestraintPoint:
    return RestraintPoint(
        position=Length(position),
        top_flange_lateral=top,
        bottom_flange_lateral=bottom,
        torsional=torsional,
        warping=warping,
        restraint_id=name,
    )


def test_each_segment_uses_its_own_moments_cb_demand_and_resistance():
    beam = response()
    segments = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(200, "B"), restraint(600, "C")),
    )
    calls = []

    def provider(segment, cb):
        calls.append((segment.segment_id, cb))
        return Moment(10_000 * cb)

    checks = evaluate_flt_segments(beam, segments, provider, rm=1.0)

    assert len(checks) == 2
    assert calls[0][0] == "SEG-001"
    assert calls[1][0] == "SEG-002"
    assert calls[0][1] == pytest.approx(checks[0].moment_data.cb)
    assert calls[1][1] == pytest.approx(checks[1].moment_data.cb)
    assert checks[0].moment_data.cb != pytest.approx(checks[1].moment_data.cb)
    for check in checks:
        expected = (
            check.moment_data.mmax.kN_cm
            / (10_000 * check.moment_data.cb)
        )
        assert check.utilization == pytest.approx(expected)


def test_governing_segment_is_selected_by_utilization_not_by_largest_cb():
    beam = response()
    segments = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(200, "B"), restraint(600, "C")),
    )
    checks = evaluate_flt_segments(
        beam,
        segments,
        lambda segment, cb: Moment(
            5_000 if segment.segment_id == "SEG-002" else 20_000
        ),
        rm=1.0,
    )
    governing = governing_flt_segment(checks)
    assert governing is not None
    assert governing.moment_data.segment.segment_id == "SEG-002"


def test_one_continuously_restrained_flange_uses_specific_blocking_path():
    beam = response()
    segments = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(600, "B")),
        (
            ContinuousFlangeRestraint(
                Length(0), Length(600), Flange.TOP, "SLAB"
            ),
        ),
    )
    data = segment_moment_data(beam, segments[0], rm=1.0)
    assert data.cb is None
    assert data.status is VerificationStatus.NOT_CHECKED
    assert data.reference_item.endswith("5.4.2.4")


def test_continuous_flange_item_a_uses_signed_end_and_center_moments():
    cb = continuous_flange_cb(
        case=ContinuousFlangeCbCase.ITEM_5_4_2_4_A,
        free_flange=Flange.TOP,
        moment_start=Moment(100.0),
        moment_end=Moment(-20.0),
        moment_center=Moment(40.0),
    )
    expected = 3.0 - (2.0 / 3.0) * (20.0 / -100.0) - (
        8.0 / 3.0
    ) * (-40.0 / (-100.0 + 20.0))
    assert cb == pytest.approx(expected)


def test_continuous_flange_item_b_requires_free_flange_not_compressed_at_ends():
    assert continuous_flange_cb(
        case=ContinuousFlangeCbCase.ITEM_5_4_2_4_B,
        free_flange=Flange.TOP,
        moment_start=Moment(-10.0),
        moment_end=Moment(0.0),
        moment_center=Moment(50.0),
    ) == pytest.approx(2.0)
    with pytest.raises(ValueError, match="extremidades"):
        continuous_flange_cb(
            case=ContinuousFlangeCbCase.ITEM_5_4_2_4_B,
            free_flange=Flange.TOP,
            moment_start=Moment(10.0),
            moment_end=Moment(0.0),
            moment_center=Moment(50.0),
        )


def test_continuous_flange_item_c_returns_one_only_after_explicit_classification():
    assert continuous_flange_cb(
        case=ContinuousFlangeCbCase.ITEM_5_4_2_4_C,
        free_flange=Flange.BOTTOM,
        moment_start=Moment(-10.0),
        moment_end=Moment(10.0),
        moment_center=Moment(-20.0),
    ) == pytest.approx(1.0)


def test_continuous_flange_segment_uses_free_flange_compression_as_demand():
    beam = response()
    segment = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(600, "B")),
        (
            ContinuousFlangeRestraint(
                Length(0), Length(600), Flange.BOTTOM, "SLAB"
            ),
        ),
    )[0]
    data = segment_moment_data(
        beam,
        segment,
        continuous_case=ContinuousFlangeCbCase.ITEM_5_4_2_4_C,
    )
    assert data.status is VerificationStatus.PASS
    assert data.cb == pytest.approx(1.0)
    assert data.mmax.kN_cm == pytest.approx(beam.maximum_moment.value)


def test_load_above_mid_depth_requires_external_stability_evidence():
    beam = response()
    segments = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(600, "B")),
        load_application_height=LoadApplicationHeight.ABOVE_MID_DEPTH,
    )
    data = segment_moment_data(beam, segments[0], rm=1.0)
    assert data.status is VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED
    assert data.cb is None


def test_reversal_identifies_both_possible_compressed_flanges():
    beam = analyze_prismatic_beam(
        BeamModel(Length(500), SupportCondition.FIXED_FIXED),
        (UniformLineLoad(Length(0), Length(500), LineLoad(0.1)),),
        Stress(20_000),
        SecondMomentOfArea(10_000),
    )
    segment = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(500, "B")),
    )[0]
    data = segment_moment_data(beam, segment, rm=1.0)
    assert data.compressed_flange is Flange.REVERSING


def test_positive_moment_identifies_top_compressed_flange():
    beam = response()
    segment = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(600, "B")),
    )[0]
    assert (
        segment_moment_data(beam, segment, rm=1.0).compressed_flange
        is Flange.TOP
    )


def test_negative_moment_segment_identifies_bottom_compressed_flange():
    beam = analyze_prismatic_beam(
        BeamModel(Length(500), SupportCondition.FIXED_FIXED),
        (UniformLineLoad(Length(0), Length(500), LineLoad(0.1)),),
        Stress(20_000),
        SecondMomentOfArea(10_000),
    )
    segment = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(75, "B"), restraint(500, "C")),
    )[0]
    assert (
        segment_moment_data(beam, segment, rm=1.0).compressed_flange
        is Flange.BOTTOM
    )


def test_missing_lateral_restraint_of_compressed_flange_blocks_segment():
    beam = response()
    segment = build_unbraced_segments(
        beam.model.length,
        (
            selective_restraint(0, "A", top=False),
            selective_restraint(600, "B", top=False),
        ),
    )[0]
    data = segment_moment_data(beam, segment, rm=1.0)
    assert data.status is VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED
    assert data.cb is None
    assert "mesa TOP" in data.justification


def test_missing_torsional_restraint_blocks_segment():
    beam = response()
    segment = build_unbraced_segments(
        beam.model.length,
        (
            selective_restraint(0, "A", torsional=False),
            restraint(600, "B"),
        ),
    )[0]
    data = segment_moment_data(beam, segment, rm=1.0)
    assert data.status is VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED
    assert data.cb is None
    assert "torcional" in data.justification


def test_reversal_requires_both_flanges_restrained():
    beam = analyze_prismatic_beam(
        BeamModel(Length(500), SupportCondition.FIXED_FIXED),
        (UniformLineLoad(Length(0), Length(500), LineLoad(0.1)),),
        Stress(20_000),
        SecondMomentOfArea(10_000),
    )
    segment = build_unbraced_segments(
        beam.model.length,
        (
            selective_restraint(0, "A", bottom=False),
            selective_restraint(500, "B", bottom=False),
        ),
    )[0]
    data = segment_moment_data(beam, segment, rm=1.0)
    assert data.compressed_flange is Flange.REVERSING
    assert data.status is VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED


@pytest.mark.parametrize(
    "support",
    (SupportCondition.CANTILEVER, SupportCondition.PROPPED_CANTILEVER),
)
def test_special_support_conditions_never_bypass_segment_classification(support):
    beam = analyze_prismatic_beam(
        BeamModel(Length(500), support),
        (UniformLineLoad(Length(0), Length(500), LineLoad(0.1)),),
        Stress(20_000),
        SecondMomentOfArea(10_000),
    )
    segment = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(500, "B")),
    )[0]
    data = segment_moment_data(beam, segment, rm=1.0)
    if support is SupportCondition.CANTILEVER:
        assert data.status is VerificationStatus.NOT_CHECKED
        assert data.cb is None
    else:
        assert data.compressed_flange in {
            Flange.TOP,
            Flange.BOTTOM,
            Flange.REVERSING,
        }
        assert data.cb is not None


def test_segments_require_unique_end_restraints():
    with pytest.raises(ValueError, match="duplicadas"):
        build_unbraced_segments(
            Length(600),
            (restraint(0, "A"), restraint(0, "B"), restraint(600, "C")),
        )


def test_rm_is_mandatory_and_never_assumed_silently():
    beam = response()
    segment = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(600, "B")),
    )[0]
    data = segment_moment_data(beam, segment)
    assert data.status is VerificationStatus.NOT_CHECKED
    assert data.cb is None
    assert "Rm" in data.justification


def test_cb_includes_explicit_rm_without_non_normative_cap():
    beam = response()
    segment = build_unbraced_segments(
        beam.model.length,
        (restraint(0, "A"), restraint(600, "B")),
    )[0]
    base = segment_moment_data(beam, segment, rm=1.0)
    modified = segment_moment_data(beam, segment, rm=2.5)
    assert base.cb is not None
    assert modified.cb == pytest.approx(2.5 * base.cb)
