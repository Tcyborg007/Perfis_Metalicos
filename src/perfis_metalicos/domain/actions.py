"""Ações e carregamentos tipados, independentes de coeficientes normativos."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from perfis_metalicos.domain.status import NormativeReference
from perfis_metalicos.domain.units import Force, Length, LineLoad, Moment


class ActionKind(Enum):
    PERMANENT_DIRECT = "PERMANENT_DIRECT"
    PERMANENT_INDIRECT = "PERMANENT_INDIRECT"
    VARIABLE = "VARIABLE"
    EXCEPTIONAL = "EXCEPTIONAL"


class EffectNature(Enum):
    UNFAVORABLE = "UNFAVORABLE"
    FAVORABLE = "FAVORABLE"
    ENVELOPE = "ENVELOPE"


class StructuralLoad(Protocol):
    def scaled(self, factor: float) -> StructuralLoad: ...


@dataclass(frozen=True, slots=True)
class UniformLineLoad:
    start: Length
    end: Length
    intensity: LineLoad

    def __post_init__(self) -> None:
        if self.end.cm <= self.start.cm:
            raise ValueError("O fim da carga uniforme deve estar após o início.")

    def scaled(self, factor: float) -> UniformLineLoad:
        return UniformLineLoad(
            self.start,
            self.end,
            LineLoad(self.intensity.kN_per_cm * float(factor)),
        )


@dataclass(frozen=True, slots=True)
class LinearlyVaryingLoad:
    start: Length
    end: Length
    start_intensity: LineLoad
    end_intensity: LineLoad

    def __post_init__(self) -> None:
        if self.end.cm <= self.start.cm:
            raise ValueError("O fim da carga variável deve estar após o início.")

    def scaled(self, factor: float) -> LinearlyVaryingLoad:
        multiplier = float(factor)
        return LinearlyVaryingLoad(
            self.start,
            self.end,
            LineLoad(self.start_intensity.kN_per_cm * multiplier),
            LineLoad(self.end_intensity.kN_per_cm * multiplier),
        )


@dataclass(frozen=True, slots=True)
class ConcentratedLoad:
    position: Length
    force: Force

    def scaled(self, factor: float) -> ConcentratedLoad:
        return ConcentratedLoad(self.position, Force(self.force.kN * float(factor)))


@dataclass(frozen=True, slots=True)
class AppliedMoment:
    position: Length
    moment: Moment

    def scaled(self, factor: float) -> AppliedMoment:
        return AppliedMoment(self.position, Moment(self.moment.kN_cm * float(factor)))


Load = UniformLineLoad | LinearlyVaryingLoad | ConcentratedLoad | AppliedMoment


@dataclass(frozen=True, slots=True)
class ActionCategory:
    category_id: str
    kind: ActionKind
    normative_reference: NormativeReference

    def __post_init__(self) -> None:
        if not self.category_id.strip():
            raise ValueError("A categoria normativa da ação é obrigatória.")


@dataclass(frozen=True, slots=True)
class ActionMetadata:
    origin: str
    document_id: str | None = None
    revision: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.origin.strip():
            raise ValueError("A origem da ação é obrigatória.")


@dataclass(frozen=True, slots=True)
class Action:
    action_id: str
    name: str
    category: ActionCategory
    loads: tuple[Load, ...]
    metadata: ActionMetadata
    effect_nature: EffectNature = EffectNature.ENVELOPE

    def __post_init__(self) -> None:
        if not self.action_id.strip() or not self.name.strip():
            raise ValueError("Identificação e nome da ação são obrigatórios.")
        if not self.loads:
            raise ValueError("Cada ação deve conter ao menos um carregamento.")

