"""Estados seguros e resultados auditáveis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Iterable, Mapping


APPROVED_SCOPE_TEXT = "APROVADO NO ESCOPO COMPUTACIONAL DECLARADO"


class VerificationStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_CHECKED = "NOT_CHECKED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    INVALID_INPUT = "INVALID_INPUT"
    EXTERNAL_EVIDENCE_REQUIRED = "EXTERNAL_EVIDENCE_REQUIRED"


@dataclass(frozen=True, slots=True)
class NormativeReference:
    standard: str
    item: str
    edition: str
    amendment_or_errata: str | None = None
    page: int | None = None
    review_status: str = "NORMATIVE_REVIEW_REQUIRED"

    def __post_init__(self) -> None:
        if not self.standard.strip() or not self.item.strip() or not self.edition.strip():
            raise ValueError("Norma, item e edição são obrigatórios.")
        if self.page is not None and self.page <= 0:
            raise ValueError("A página normativa deve ser positiva.")


@dataclass(frozen=True, slots=True)
class VerificationResult:
    check_id: str
    demand: Any | None
    resistance_or_limit: Any | None
    utilization: float | None
    status: VerificationStatus
    justification: str
    normative_references: tuple[NormativeReference, ...] = ()
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    numerical_tolerance: float | None = None
    combination: str | None = None
    position: Any | None = None
    segment: str | None = None
    engine_version: str = "0.1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise ValueError("check_id é obrigatório.")
        if not self.justification.strip():
            raise ValueError("A justificativa é obrigatória.")
        if self.utilization is not None:
            if not math.isfinite(self.utilization) or self.utilization < 0:
                raise ValueError("A utilização deve ser finita e não negativa.")
        if self.numerical_tolerance is not None:
            if not math.isfinite(self.numerical_tolerance) or self.numerical_tolerance < 0:
                raise ValueError("A tolerância deve ser finita e não negativa.")
        if self.status is VerificationStatus.PASS:
            if self.demand is None or self.resistance_or_limit is None:
                raise ValueError("PASS exige solicitação e resistência ou limite.")
            if self.utilization is None:
                raise ValueError("PASS exige utilização.")
        if self.status is VerificationStatus.NOT_APPLICABLE and not self.assumptions:
            raise ValueError("NOT_APPLICABLE exige a hipótese que comprova a não aplicabilidade.")


@dataclass(frozen=True, slots=True)
class GlobalVerificationResult:
    status: VerificationStatus
    display_text: str
    checks: tuple[VerificationResult, ...]
    blockers: tuple[VerificationResult, ...]
    failures: tuple[VerificationResult, ...]

    @property
    def is_approved_in_declared_scope(self) -> bool:
        return self.status is VerificationStatus.PASS


_BLOCKING_PRIORITY = (
    VerificationStatus.INVALID_INPUT,
    VerificationStatus.OUT_OF_SCOPE,
    VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED,
    VerificationStatus.NOT_CHECKED,
)


def aggregate_verifications(
    checks: Iterable[VerificationResult],
) -> GlobalVerificationResult:
    values = tuple(checks)
    if not values:
        raise ValueError("Ao menos uma verificação é obrigatória.")

    failures = tuple(item for item in values if item.status is VerificationStatus.FAIL)
    blockers = tuple(
        item
        for item in values
        if item.status
        in {
            VerificationStatus.NOT_CHECKED,
            VerificationStatus.OUT_OF_SCOPE,
            VerificationStatus.INVALID_INPUT,
            VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED,
        }
    )

    if failures:
        status = VerificationStatus.FAIL
        text = "REPROVADO"
    elif blockers:
        status = next(
            candidate
            for candidate in _BLOCKING_PRIORITY
            if any(item.status is candidate for item in blockers)
        )
        text = status.value
    elif all(
        item.status in {VerificationStatus.PASS, VerificationStatus.NOT_APPLICABLE}
        for item in values
    ):
        status = VerificationStatus.PASS
        text = APPROVED_SCOPE_TEXT
    else:
        status = VerificationStatus.NOT_CHECKED
        text = VerificationStatus.NOT_CHECKED.value

    return GlobalVerificationResult(
        status=status,
        display_text=text,
        checks=values,
        blockers=blockers,
        failures=failures,
    )

