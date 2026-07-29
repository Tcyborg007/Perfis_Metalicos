"""Núcleo auditável do projeto Perfis Metálicos."""

from perfis_metalicos.domain.status import (
    APPROVED_SCOPE_TEXT,
    GlobalVerificationResult,
    VerificationResult,
    VerificationStatus,
    aggregate_verifications,
)

__all__ = [
    "APPROVED_SCOPE_TEXT",
    "GlobalVerificationResult",
    "VerificationResult",
    "VerificationStatus",
    "aggregate_verifications",
]

__version__ = "0.1.0"

