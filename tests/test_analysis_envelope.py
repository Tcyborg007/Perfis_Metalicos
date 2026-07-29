import pytest

from perfis_metalicos.analysis import analyze_combination_envelope
from perfis_metalicos.combinations import (
    CombinationFamily,
    LoadCombination,
)
from perfis_metalicos.combinations.generator import CombinationTerm, TermRole
from perfis_metalicos.domain import (
    Action,
    ActionCategory,
    ActionKind,
    ActionMetadata,
    BeamModel,
    EffectNature,
    Length,
    LineLoad,
    NormativeReference,
    SecondMomentOfArea,
    Stress,
    SupportCondition,
    UniformLineLoad,
)

REFERENCE = NormativeReference(
    standard="TEST_ONLY",
    item="SYNTHETIC",
    edition="0",
    review_status="TEST_ONLY",
)


def combination(identifier: str, intensity: float) -> LoadCombination:
    action = Action(
        action_id=f"A-{identifier}",
        name="Carga sintética",
        category=ActionCategory("TEST", ActionKind.VARIABLE, REFERENCE),
        loads=(
            UniformLineLoad(
                Length(0.0),
                Length(400.0),
                LineLoad(intensity),
            ),
        ),
        metadata=ActionMetadata(origin="TEST_ONLY"),
        effect_nature=EffectNature.UNFAVORABLE,
    )
    return LoadCombination(
        combination_id=identifier,
        family=CombinationFamily.ULTIMATE_NORMAL,
        leading_action_id=action.action_id,
        terms=(CombinationTerm(action, 1.0, TermRole.LEADING_VARIABLE, REFERENCE),),
        rule_set_id="TEST_ONLY",
        normative_decision_id="TEST_ONLY",
    )


def test_envelope_keeps_governing_combination_and_position():
    envelope = analyze_combination_envelope(
        BeamModel(Length(400.0), SupportCondition.SIMPLY_SUPPORTED),
        (combination("LIGHT", 0.04), combination("HEAVY", 0.09)),
        Stress(20000.0),
        SecondMomentOfArea(8000.0),
    )
    assert envelope.absolute_maximum_moment.combination_id == "HEAVY"
    assert envelope.absolute_maximum_moment.position.cm == pytest.approx(
        200.0,
        abs=1e-9,
    )
    assert envelope.absolute_maximum_shear.combination_id == "HEAVY"
    assert envelope.absolute_maximum_deflection.combination_id == "HEAVY"
    assert len(envelope.analyses) == 2


def test_envelope_rejects_empty_or_duplicate_identifiers():
    model = BeamModel(Length(400.0), SupportCondition.SIMPLY_SUPPORTED)
    material = Stress(20000.0)
    inertia = SecondMomentOfArea(8000.0)
    try:
        analyze_combination_envelope(model, (), material, inertia)
    except ValueError as error:
        assert "Ao menos uma combinação" in str(error)
    else:
        raise AssertionError("Envelope vazio deveria ser rejeitado.")

    duplicate = combination("DUPLICATE", 0.04)
    try:
        analyze_combination_envelope(
            model,
            (duplicate, duplicate),
            material,
            inertia,
        )
    except ValueError as error:
        assert "combination_id deve ser único" in str(error)
    else:
        raise AssertionError("Identificadores duplicados deveriam ser rejeitados.")


def test_envelope_rejects_any_unconverged_combination():
    try:
        analyze_combination_envelope(
            BeamModel(Length(400.0), SupportCondition.SIMPLY_SUPPORTED),
            (combination("STRICT", 0.09),),
            Stress(20000.0),
            SecondMomentOfArea(8000.0),
            relative_tolerance=1e-16,
            max_refinements=2,
        )
    except RuntimeError as error:
        assert "STRICT" in str(error)
        assert "falta de convergência" in str(error)
    else:
        raise AssertionError("Combinação sem convergência não pode compor o envelope.")
