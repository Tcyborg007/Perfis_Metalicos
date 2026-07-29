import pytest

from perfis_metalicos.combinations import (
    CombinationFamily,
    CombinationRuleSet,
    FactorRule,
    TermRole,
    generate_combinations,
)
from perfis_metalicos.domain import (
    Action,
    ActionCategory,
    ActionKind,
    ActionMetadata,
    ConcentratedLoad,
    EffectNature,
    Force,
    Length,
    LineLoad,
    NormativeReference,
    UniformLineLoad,
)

TEST_REFERENCE = NormativeReference(
    standard="TEST_ONLY",
    item="synthetic",
    edition="0",
    review_status="TEST_ONLY",
)


def category(category_id: str, kind: ActionKind) -> ActionCategory:
    return ActionCategory(category_id, kind, TEST_REFERENCE)


def action(
    action_id: str,
    category_id: str,
    kind: ActionKind,
    nature: EffectNature = EffectNature.UNFAVORABLE,
) -> Action:
    return Action(
        action_id=action_id,
        name=action_id,
        category=category(category_id, kind),
        loads=(
            UniformLineLoad(
                Length(0),
                Length(500),
                LineLoad(0.01),
            ),
        ),
        metadata=ActionMetadata(origin="TEST_ONLY"),
        effect_nature=nature,
    )


def rule(
    category_id: str,
    family: CombinationFamily,
    role: TermRole,
    unfavorable: float,
    favorable: float | None = None,
    reviewed: bool = True,
) -> FactorRule:
    return FactorRule(
        category_id=category_id,
        family=family,
        role=role,
        unfavorable_factor=unfavorable,
        favorable_factor=unfavorable if favorable is None else favorable,
        reference=TEST_REFERENCE,
        reviewed=reviewed,
    )


def test_each_variable_becomes_leader_and_coefficients_keep_their_source():
    family = CombinationFamily.ULTIMATE_NORMAL
    actions = (
        action("G", "PERM", ActionKind.PERMANENT_DIRECT),
        action("Q1", "LIVE", ActionKind.VARIABLE),
        action("Q2", "WIND", ActionKind.VARIABLE),
    )
    rules = CombinationRuleSet(
        "TEST_RULES",
        (
            rule("PERM", family, TermRole.PERMANENT, 1.2),
            rule("LIVE", family, TermRole.LEADING_VARIABLE, 1.5),
            rule("LIVE", family, TermRole.ACCOMPANYING_VARIABLE, 0.9),
            rule("WIND", family, TermRole.LEADING_VARIABLE, 1.4),
            rule("WIND", family, TermRole.ACCOMPANYING_VARIABLE, 0.7),
        ),
        normative_decision_id="TEST_ONLY",
    )

    combinations = generate_combinations(actions, family, rules)

    assert [item.leading_action_id for item in combinations] == ["Q1", "Q2"]
    q1 = combinations[0]
    assert {term.action.action_id: term.factor for term in q1.terms} == {
        "G": 1.2,
        "Q1": 1.5,
        "Q2": 0.7,
    }
    assert all(coefficient[2] == "synthetic" for coefficient in q1.coefficients)


def test_envelope_generates_favorable_and_unfavorable_permanent_variants():
    family = CombinationFamily.ULTIMATE_NORMAL
    actions = (
        action(
            "G",
            "PERM",
            ActionKind.PERMANENT_DIRECT,
            nature=EffectNature.ENVELOPE,
        ),
        action("Q", "LIVE", ActionKind.VARIABLE),
    )
    rules = CombinationRuleSet(
        "TEST_RULES",
        (
            rule("PERM", family, TermRole.PERMANENT, 1.3, favorable=0.9),
            rule("LIVE", family, TermRole.LEADING_VARIABLE, 1.5),
        ),
        normative_decision_id="TEST_ONLY",
    )

    combinations = generate_combinations(actions, family, rules)
    assert len(combinations) == 2
    assert {
        next(term.factor for term in item.terms if term.action.action_id == "G")
        for item in combinations
    } == {0.9, 1.3}


def test_quasi_permanent_service_combination_has_no_leader():
    family = CombinationFamily.SERVICE_QUASI_PERMANENT
    actions = (
        action("G", "PERM", ActionKind.PERMANENT_DIRECT),
        action("Q1", "LIVE", ActionKind.VARIABLE),
        action("Q2", "WIND", ActionKind.VARIABLE),
    )
    rules = CombinationRuleSet(
        "TEST_RULES",
        (
            rule("PERM", family, TermRole.PERMANENT, 1.0),
            rule("LIVE", family, TermRole.ACCOMPANYING_VARIABLE, 0.3),
            rule("WIND", family, TermRole.ACCOMPANYING_VARIABLE, 0.2),
        ),
        normative_decision_id="TEST_ONLY",
    )

    combinations = generate_combinations(actions, family, rules)
    assert len(combinations) == 1
    assert combinations[0].leading_action_id is None
    assert {term.factor for term in combinations[0].terms} == {1.0, 0.3, 0.2}


def test_exceptional_family_requires_and_alternates_exceptional_actions():
    family = CombinationFamily.ULTIMATE_EXCEPTIONAL
    actions = (
        action("G", "PERM", ActionKind.PERMANENT_DIRECT),
        action("Q", "LIVE", ActionKind.VARIABLE),
        Action(
            action_id="A",
            name="A",
            category=category("ACC", ActionKind.EXCEPTIONAL),
            loads=(ConcentratedLoad(Length(250), Force(100)),),
            metadata=ActionMetadata(origin="TEST_ONLY"),
            effect_nature=EffectNature.UNFAVORABLE,
        ),
    )
    rules = CombinationRuleSet(
        "TEST_RULES",
        (
            rule("PERM", family, TermRole.PERMANENT, 1.0),
            rule("LIVE", family, TermRole.ACCOMPANYING_VARIABLE, 0.4),
            rule("ACC", family, TermRole.EXCEPTIONAL, 1.0),
        ),
        normative_decision_id="TEST_ONLY",
    )
    combinations = generate_combinations(actions, family, rules)
    assert len(combinations) == 1
    assert combinations[0].leading_action_id == "A"
    assert len(combinations[0].loads) == 3


def test_unknown_or_unreviewed_category_is_rejected():
    family = CombinationFamily.ULTIMATE_NORMAL
    actions = (action("Q", "UNKNOWN", ActionKind.VARIABLE),)
    missing_rules = CombinationRuleSet(
        "TEST_RULES",
        (),
        normative_decision_id="TEST_ONLY",
    )
    with pytest.raises(ValueError, match="Categoria sem regra"):
        generate_combinations(actions, family, missing_rules)

    unreviewed = CombinationRuleSet(
        "TEST_RULES",
        (
            rule(
                "UNKNOWN",
                family,
                TermRole.LEADING_VARIABLE,
                1.0,
                reviewed=False,
            ),
        ),
        normative_decision_id="TEST_ONLY",
    )
    with pytest.raises(ValueError, match="requer revisão normativa"):
        generate_combinations(actions, family, unreviewed)

