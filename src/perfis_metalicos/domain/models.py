"""Entradas estruturais tipadas, sem equações normativas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from perfis_metalicos.domain.units import (
    Area,
    Length,
    SecondMomentOfArea,
    SectionModulus,
    Stress,
    WarpingConstant,
)


class SupportCondition(Enum):
    SIMPLY_SUPPORTED = "SIMPLY_SUPPORTED"
    CANTILEVER = "CANTILEVER"
    FIXED_FIXED = "FIXED_FIXED"
    PROPPED_CANTILEVER = "PROPPED_CANTILEVER"


@dataclass(frozen=True, slots=True)
class BeamModel:
    length: Length
    support: SupportCondition

    def __post_init__(self) -> None:
        self.length.require_positive("Vão")


@dataclass(frozen=True, slots=True)
class SteelMaterial:
    fy: Stress
    fu: Stress
    elastic_modulus: Stress
    specification: str
    source_document: str | None = None

    def __post_init__(self) -> None:
        self.fy.require_positive("fy")
        self.fu.require_positive("fu")
        self.elastic_modulus.require_positive("E")
        if not self.specification.strip():
            raise ValueError("A especificação do aço é obrigatória.")


@dataclass(frozen=True, slots=True)
class ISectionProperties:
    designation: str
    d: Length
    bf: Length
    tw: Length
    tf: Length
    h_faces: Length
    h_clear: Length
    area: Area
    ix: SecondMomentOfArea
    iy: SecondMomentOfArea
    wx: SectionModulus
    zx: SectionModulus
    torsion_constant: SecondMomentOfArea
    warping_constant: WarpingConstant
    catalog_source_id: str | None = None

    def __post_init__(self) -> None:
        if not self.designation.strip():
            raise ValueError("A designação do perfil é obrigatória.")
        for name in ("d", "bf", "tw", "tf", "h_faces", "h_clear"):
            getattr(self, name).require_positive(name)
        self.area.require_positive()
        self.ix.require_positive("Ix")
        self.iy.require_positive("Iy")
        self.wx.require_positive("Wx")
        self.zx.require_positive("Zx")
        self.torsion_constant.require_positive("J")
        self.warping_constant.require_positive("Cw")
        if self.h_clear.cm >= self.d.cm:
            raise ValueError("A altura livre da alma deve ser menor que a altura total.")
        if self.zx.cm3 < self.wx.cm3:
            raise ValueError("Zx não pode ser menor que Wx.")

