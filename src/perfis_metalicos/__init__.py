"""Núcleo auditável do projeto Perfis Metálicos."""

from perfis_metalicos.domain.status import (
    APPROVED_SCOPE_TEXT,
    GlobalVerificationResult,
    VerificationResult,
    VerificationStatus,
    aggregate_verifications,
)
from perfis_metalicos.version import ENGINE_VERSION

__all__ = [
    "APPROVED_SCOPE_TEXT",
    "GlobalVerificationResult",
    "VerificationResult",
    "VerificationStatus",
    "aggregate_verifications",
    "ENGINE_VERSION",
]

__version__ = ENGINE_VERSION
