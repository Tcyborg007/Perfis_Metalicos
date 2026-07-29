from datetime import date
import math

import pytest

from perfis_metalicos.audit import ExternalEvidence
from perfis_metalicos.domain import (
    APPROVED_SCOPE_TEXT,
    Area,
    Force,
    ISectionProperties,
    Length,
    Moment,
    NormativeReference,
    SecondMomentOfArea,
    SectionModulus,
    Stress,
    VerificationResult,
    VerificationStatus,
    WarpingConstant,
    aggregate_verifications,
)


def result(status: VerificationStatus, check_id: str = "check") -> VerificationResult:
    common = {
        "check_id": check_id,
        "demand": Force(10.0),
        "resistance_or_limit": Force(20.0),
        "utilization": 0.5,
        "status": status,
        "justification": "Caso de teste.",
    }
    if status is VerificationStatus.NOT_APPLICABLE:
        common["assumptions"] = ("Aplicabilidade excluída por hipótese explícita.",)
    return VerificationResult(**common)


def test_unit_conversions_are_explicit_and_reversible():
    assert Length.from_mm(500.0).cm == pytest.approx(50.0)
    assert Length.from_m(5.0).cm == pytest.approx(500.0)
    assert Moment.from_kN_m(12.5).kN_cm == pytest.approx(1250.0)
    assert Stress.from_mpa(345.0).kN_per_cm2 == pytest.approx(34.5)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_units_reject_non_finite_values(value):
    with pytest.raises(ValueError):
        Length(value)


def test_typed_section_rejects_inconsistent_geometry_and_moduli():
    with pytest.raises(ValueError, match="altura livre"):
        ISectionProperties(
            designation="X",
            d=Length(50),
            bf=Length(20),
            tw=Length(0.8),
            tf=Length(1.2),
            h_faces=Length(47.6),
            h_clear=Length(50),
            area=Area(100),
            ix=SecondMomentOfArea(10_000),
            iy=SecondMomentOfArea(500),
            wx=SectionModulus(400),
            zx=SectionModulus(450),
            torsion_constant=SecondMomentOfArea(20),
            warping_constant=WarpingConstant(300_000),
        )


def test_pass_requires_demand_resistance_and_utilization():
    with pytest.raises(ValueError, match="PASS exige"):
        VerificationResult(
            check_id="unsafe-pass",
            demand=None,
            resistance_or_limit=None,
            utilization=None,
            status=VerificationStatus.PASS,
            justification="Não pode ser aprovado.",
        )


def test_not_applicable_requires_explicit_assumption():
    with pytest.raises(ValueError, match="NOT_APPLICABLE"):
        VerificationResult(
            check_id="na",
            demand=None,
            resistance_or_limit=None,
            utilization=None,
            status=VerificationStatus.NOT_APPLICABLE,
            justification="Sem hipótese.",
        )


def test_global_approval_uses_required_scoped_expression():
    global_result = aggregate_verifications(
        [result(VerificationStatus.PASS), result(VerificationStatus.NOT_APPLICABLE, "na")]
    )
    assert global_result.status is VerificationStatus.PASS
    assert global_result.display_text == APPROVED_SCOPE_TEXT
    assert global_result.is_approved_in_declared_scope


@pytest.mark.parametrize(
    "blocking",
    [
        VerificationStatus.NOT_CHECKED,
        VerificationStatus.OUT_OF_SCOPE,
        VerificationStatus.INVALID_INPUT,
        VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED,
    ],
)
def test_any_mandatory_blocker_prevents_global_approval(blocking):
    global_result = aggregate_verifications(
        [result(VerificationStatus.PASS), result(blocking, "blocking")]
    )
    assert not global_result.is_approved_in_declared_scope
    assert global_result.status is blocking
    assert global_result.display_text != APPROVED_SCOPE_TEXT


def test_failure_is_reported_without_hiding_simultaneous_pending_items():
    global_result = aggregate_verifications(
        [
            result(VerificationStatus.FAIL, "failure"),
            result(VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED, "pending"),
        ]
    )
    assert global_result.status is VerificationStatus.FAIL
    assert global_result.display_text == "REPROVADO"
    assert [item.check_id for item in global_result.failures] == ["failure"]
    assert [item.check_id for item in global_result.blockers] == ["pending"]


def test_external_evidence_requires_traceable_sha256_and_checked_items():
    evidence = ExternalEvidence(
        document_id="MEM-001",
        revision="R0",
        responsible_engineer="Engenheira Exemplo",
        professional_registration="CREA-UF 000000",
        date=date(2026, 7, 29),
        file_hash="a" * 64,
        checked_items=("ELS_DEFLECTION", "LOCAL_FORCES"),
    )
    assert evidence.checked_items == ("ELS_DEFLECTION", "LOCAL_FORCES")

    with pytest.raises(ValueError, match="SHA-256"):
        ExternalEvidence(
            document_id="MEM-001",
            revision="R0",
            responsible_engineer="Engenheira Exemplo",
            professional_registration="CREA-UF 000000",
            date=date(2026, 7, 29),
            file_hash="not-a-hash",
            checked_items=("ELS_DEFLECTION",),
        )


def test_normative_reference_never_defaults_to_an_unverified_item():
    reference = NormativeReference(
        standard="ABNT NBR 8800",
        item="5.4.2",
        edition="2024",
    )
    assert reference.review_status == "NORMATIVE_REVIEW_REQUIRED"

