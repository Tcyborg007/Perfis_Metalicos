"""Tipos de domínio, unidades e estados de verificação."""

from perfis_metalicos.domain.models import (
    BeamModel,
    ISectionProperties,
    SteelMaterial,
    SupportCondition,
)
from perfis_metalicos.domain.status import (
    APPROVED_SCOPE_TEXT,
    GlobalVerificationResult,
    NormativeReference,
    VerificationResult,
    VerificationStatus,
    aggregate_verifications,
)
from perfis_metalicos.domain.units import (
    Area,
    Force,
    Length,
    LineLoad,
    Moment,
    SecondMomentOfArea,
    SectionModulus,
    Stress,
    WarpingConstant,
)

__all__ = [
    "APPROVED_SCOPE_TEXT",
    "Area",
    "BeamModel",
    "Force",
    "GlobalVerificationResult",
    "ISectionProperties",
    "Length",
    "LineLoad",
    "Moment",
    "NormativeReference",
    "SecondMomentOfArea",
    "SectionModulus",
    "SteelMaterial",
    "Stress",
    "SupportCondition",
    "VerificationResult",
    "VerificationStatus",
    "WarpingConstant",
    "aggregate_verifications",
]

