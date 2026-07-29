"""Grandezas explícitas na política canônica kN-cm.

Os construtores nomeados são as únicas conversões previstas no domínio. Isso evita
que números sem unidade atravessem as fronteiras entre interface e cálculo.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


def _finite(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} deve ser finito.")
    return number


@dataclass(frozen=True, slots=True)
class Length:
    cm: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "cm", _finite(self.cm, "Comprimento"))

    @classmethod
    def from_mm(cls, value: float) -> "Length":
        return cls(_finite(value, "Comprimento") / 10.0)

    @classmethod
    def from_m(cls, value: float) -> "Length":
        return cls(_finite(value, "Comprimento") * 100.0)

    @property
    def mm(self) -> float:
        return self.cm * 10.0

    @property
    def m(self) -> float:
        return self.cm / 100.0

    def require_positive(self, name: str = "Comprimento") -> "Length":
        if self.cm <= 0:
            raise ValueError(f"{name} deve ser positivo.")
        return self


@dataclass(frozen=True, slots=True)
class Force:
    kN: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "kN", _finite(self.kN, "Força"))


@dataclass(frozen=True, slots=True)
class Moment:
    kN_cm: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "kN_cm", _finite(self.kN_cm, "Momento"))

    @classmethod
    def from_kN_m(cls, value: float) -> "Moment":
        return cls(_finite(value, "Momento") * 100.0)

    @property
    def kN_m(self) -> float:
        return self.kN_cm / 100.0


@dataclass(frozen=True, slots=True)
class LineLoad:
    kN_per_cm: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "kN_per_cm", _finite(self.kN_per_cm, "Carga linear"))

    @classmethod
    def from_kN_per_m(cls, value: float) -> "LineLoad":
        return cls(_finite(value, "Carga linear") / 100.0)

    @property
    def kN_per_m(self) -> float:
        return self.kN_per_cm * 100.0


@dataclass(frozen=True, slots=True)
class Stress:
    kN_per_cm2: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "kN_per_cm2", _finite(self.kN_per_cm2, "Tensão"))

    @classmethod
    def from_mpa(cls, value: float) -> "Stress":
        return cls(_finite(value, "Tensão") / 10.0)

    @property
    def mpa(self) -> float:
        return self.kN_per_cm2 * 10.0

    def require_positive(self, name: str = "Tensão") -> "Stress":
        if self.kN_per_cm2 <= 0:
            raise ValueError(f"{name} deve ser positiva.")
        return self


@dataclass(frozen=True, slots=True)
class Area:
    cm2: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "cm2", _finite(self.cm2, "Área"))

    def require_positive(self, name: str = "Área") -> "Area":
        if self.cm2 <= 0:
            raise ValueError(f"{name} deve ser positiva.")
        return self


@dataclass(frozen=True, slots=True)
class SecondMomentOfArea:
    cm4: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "cm4", _finite(self.cm4, "Momento de inércia"))

    def require_positive(self, name: str = "Momento de inércia") -> "SecondMomentOfArea":
        if self.cm4 <= 0:
            raise ValueError(f"{name} deve ser positivo.")
        return self


@dataclass(frozen=True, slots=True)
class SectionModulus:
    cm3: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "cm3", _finite(self.cm3, "Módulo de seção"))

    def require_positive(self, name: str = "Módulo de seção") -> "SectionModulus":
        if self.cm3 <= 0:
            raise ValueError(f"{name} deve ser positivo.")
        return self


@dataclass(frozen=True, slots=True)
class WarpingConstant:
    cm6: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "cm6", _finite(self.cm6, "Constante de empenamento"))

    def require_positive(self, name: str = "Constante de empenamento") -> "WarpingConstant":
        if self.cm6 <= 0:
            raise ValueError(f"{name} deve ser positiva.")
        return self

