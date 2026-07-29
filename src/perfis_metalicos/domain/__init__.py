"""Tipos de domínio, unidades e estados de verificação."""

from perfis_metalicos.domain.actions import (
    Action,
    ActionCategory,
    ActionKind,
    ActionMetadata,
    AppliedMoment,
    ConcentratedLoad,
    EffectNature,
    LinearlyVaryingLoad,
    UniformLineLoad,
)
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
    "Action",
    "ActionCategory",
    "ActionKind",
    "ActionMetadata",
    "Area",
    "AppliedMoment",
    "BeamModel",
    "ConcentratedLoad",
    "EffectNature",
    "Force",
    "GlobalVerificationResult",
    "ISectionProperties",
    "Length",
    "LinearlyVaryingLoad",
    "LineLoad",
    "Moment",
    "NormativeReference",
    "SecondMomentOfArea",
    "SectionModulus",
    "SteelMaterial",
    "Stress",
    "SupportCondition",
    "UniformLineLoad",
    "VerificationResult",
    "VerificationStatus",
    "WarpingConstant",
    "aggregate_verifications",
]
