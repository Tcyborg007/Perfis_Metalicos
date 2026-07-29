import pytest

from perfis_metalicos.checks import (
    ConstructionPhaseDeflection,
    DeflectionCriterion,
    ServiceabilityLimit,
    ServiceCombinationFamily,
    evaluate_serviceability_deflection,
    vibration_out_of_scope_result,
)
from perfis_metalicos.domain import Length, NormativeReference, VerificationStatus


def phase():
    return ConstructionPhaseDeflection(
        phase_id="PHASE-02-AFTER-PARTITIONS",
        permanent_before_fragile=Length(0.40),
        permanent_after_fragile=Length(0.20),
        leading_variable=Length(0.50),
        accompanying_variables=Length(0.10),
        relative_between_points=Length(0.35),
    )


def limit(criterion, review_status="SOURCE_VERIFIED"):
    return ServiceabilityLimit(
        criterion=criterion,
        limit=Length(1.0),
        sensitive_element="Alvenaria não estrutural",
        reference=NormativeReference(
            standard="TEST_STANDARD",
            edition="TEST_ONLY",
            item="TEST_ITEM",
            review_status=review_status,
        ),
    )


@pytest.mark.parametrize(
    ("criterion", "expected"),
    (
        (DeflectionCriterion.TOTAL, 1.20),
        (DeflectionCriterion.AFTER_FRAGILE_ELEMENT, 0.80),
        (DeflectionCriterion.VARIABLE_COMPONENT, 0.60),
        (DeflectionCriterion.RELATIVE_BETWEEN_POINTS, 0.35),
    ),
)
def test_each_deflection_component_is_kept_separate(criterion, expected):
    result = evaluate_serviceability_deflection(
        check_id=f"ELS-{criterion.value}",
        phase=phase(),
        combination=ServiceCombinationFamily.RARE,
        limit=limit(criterion),
    )
    assert result.demand.cm == pytest.approx(expected)
    assert result.metadata["phase"] == "PHASE-02-AFTER-PARTITIONS"


def test_camber_reduces_only_total_criterion():
    total = evaluate_serviceability_deflection(
        check_id="ELS-TOTAL",
        phase=phase(),
        combination=ServiceCombinationFamily.QUASI_PERMANENT,
        limit=limit(DeflectionCriterion.TOTAL),
        camber=Length(0.30),
    )
    after_fragile = evaluate_serviceability_deflection(
        check_id="ELS-AFTER",
        phase=phase(),
        combination=ServiceCombinationFamily.FREQUENT,
        limit=limit(DeflectionCriterion.AFTER_FRAGILE_ELEMENT),
        camber=Length(0.30),
    )
    assert total.demand.cm == pytest.approx(0.90)
    assert after_fragile.demand.cm == pytest.approx(0.80)


def test_unreviewed_limit_never_generates_pass():
    result = evaluate_serviceability_deflection(
        check_id="ELS-UNREVIEWED",
        phase=phase(),
        combination=ServiceCombinationFamily.RARE,
        limit=limit(
            DeflectionCriterion.TOTAL,
            review_status="NORMATIVE_REVIEW_REQUIRED",
        ),
    )
    assert result.status is VerificationStatus.NOT_CHECKED


def test_vibration_is_explicitly_out_of_scope():
    assert vibration_out_of_scope_result().status is VerificationStatus.OUT_OF_SCOPE

