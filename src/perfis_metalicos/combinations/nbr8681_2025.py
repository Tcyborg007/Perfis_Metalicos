"""Catálogo controlado da ABNT NBR 8681:2025.

Os coeficientes deste módulo foram transcritos das Seções 5.1.3 a 5.1.6 e
das Tabelas 1 a 6 da cópia controlada no manifesto normativo. As regras
geradas permanecem ``reviewed=False`` até a aprovação da decisão ND-001,
que trata da compatibilidade com a ABNT NBR 8800:2024.

As duas classificações de uma ação variável são mantidas separadas:

* a categoria de ``gamma_q`` vem das Tabelas 4 ou 5;
* a categoria de ``psi`` vem da Tabela 6.

Essa separação impede, por exemplo, que "ação truncada" seja tratada
incorretamente como uma categoria de uso da edificação.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from perfis_metalicos.combinations.generator import (
    CombinationFamily,
    CombinationRuleSet,
    FactorRule,
    TermRole,
)
from perfis_metalicos.domain.actions import ActionKind
from perfis_metalicos.domain.status import NormativeReference


class ActionGrouping(Enum):
    """Opção normativa entre as Tabelas 1/4 e as Tabelas 2/5."""

    SEPARATE = "SEPARATE"
    GROUPED = "GROUPED"


class EffectiveAccompanyingFactor(Enum):
    """Fator efetivo das acompanhantes em situação transitória."""

    PSI_0 = "PSI_0"
    PSI_2_FOR_VERY_SHORT_ACTION = "PSI_2_FOR_VERY_SHORT_ACTION"


class GroupedAtmosphericTemperatureTreatment(Enum):
    """Opção da nota da Tabela 5 para a temperatura atmosférica."""

    GROUP_WITH_VARIABLE_ACTIONS = "GROUP_WITH_VARIABLE_ACTIONS"
    KEEP_SEPARATE = "KEEP_SEPARATE"


class FirePsi2Treatment(Enum):
    """Tratamento explícito da faculdade prevista na nota c da Tabela 6."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_ADOPTED = "NOT_ADOPTED"
    ADOPT_REDUCTION = "ADOPT_REDUCTION"


class NBR8681PermanentCategory(Enum):
    STEEL_SELF_WEIGHT_AND_EQUIPMENT = "G_STEEL_EQUIPMENT"
    PRECAST_WOOD_INDUSTRIALIZED = "G_PRECAST_WOOD_INDUSTRIALIZED"
    CAST_IN_PLACE = "G_CAST_IN_PLACE"
    INDUSTRIALIZED_WITH_IN_LOCO_ADDITION = "G_INDUSTRIALIZED_IN_LOCO"
    GENERAL_CONSTRUCTION_ELEMENTS = "G_GENERAL_CONSTRUCTION"
    DIRECT_PERMANENT_GROUPED = "G_DIRECT_GROUPED"
    PRESTRESSING = "G_PRESTRESSING"
    SETTLEMENT_AND_SHRINKAGE = "G_SETTLEMENT_SHRINKAGE"


class NBR8681VariableGammaCategory(Enum):
    TRUNCATED = "GAMMA_Q_TRUNCATED"
    ATMOSPHERIC_TEMPERATURE = "GAMMA_Q_ATMOSPHERIC_TEMPERATURE"
    WIND = "GAMMA_Q_WIND"
    OTHER = "GAMMA_Q_OTHER"


class NBR8681VariablePsiCategory(Enum):
    RESIDENTIAL_RESTRICTED_ACCESS = "PSI_USE_RESIDENTIAL"
    COMMERCIAL_OFFICE_PUBLIC_ACCESS = "PSI_USE_COMMERCIAL_PUBLIC"
    STORAGE_WORKSHOP_GARAGE_ROOF = "PSI_USE_STORAGE_WORKSHOP_GARAGE_ROOF"
    WIND = "PSI_WIND"
    ATMOSPHERIC_TEMPERATURE = "PSI_ATMOSPHERIC_TEMPERATURE"
    PEDESTRIAN_BRIDGE = "PSI_PEDESTRIAN_BRIDGE"
    ROAD_BRIDGE = "PSI_ROAD_BRIDGE"
    RAILWAY_BRIDGE = "PSI_RAILWAY_BRIDGE"
    CRANE_RUNWAY_BEAM = "PSI_CRANE_RUNWAY_BEAM"
    SILO_OR_RESERVOIR = "PSI_SILO_OR_RESERVOIR"


class NBR8681ExceptionalCategory(Enum):
    GENERAL = "A_EXCEPTIONAL_GENERAL"


@dataclass(frozen=True, slots=True)
class NBR8681VariableClassification:
    """Classificação completa necessária para ponderar uma ação variável."""

    gamma_category: NBR8681VariableGammaCategory
    psi_category: NBR8681VariablePsiCategory

    def __post_init__(self) -> None:
        required_pairs = {
            NBR8681VariableGammaCategory.WIND: NBR8681VariablePsiCategory.WIND,
            NBR8681VariableGammaCategory.ATMOSPHERIC_TEMPERATURE: (
                NBR8681VariablePsiCategory.ATMOSPHERIC_TEMPERATURE
            ),
        }
        required = required_pairs.get(self.gamma_category)
        if required is not None and self.psi_category is not required:
            raise ValueError(f"{self.gamma_category.value} exige {required.value}.")
        if (
            self.psi_category is NBR8681VariablePsiCategory.WIND
            and self.gamma_category is not NBR8681VariableGammaCategory.WIND
        ):
            raise ValueError("PSI_WIND exige a categoria gamma_q de vento.")
        if (
            self.psi_category is NBR8681VariablePsiCategory.ATMOSPHERIC_TEMPERATURE
            and self.gamma_category is not NBR8681VariableGammaCategory.ATMOSPHERIC_TEMPERATURE
        ):
            raise ValueError(
                "PSI_ATMOSPHERIC_TEMPERATURE exige a categoria gamma_q de temperatura atmosférica."
            )

    @property
    def category_id(self) -> str:
        return f"{self.gamma_category.value}::{self.psi_category.value}"


@dataclass(frozen=True, slots=True)
class PermanentFactors:
    category: NBR8681PermanentCategory
    normal_unfavorable: float
    normal_favorable: float
    special_unfavorable: float
    special_favorable: float
    exceptional_unfavorable: float
    exceptional_favorable: float
    table: str
    page: int


@dataclass(frozen=True, slots=True)
class VariableGammaFactors:
    category: NBR8681VariableGammaCategory
    normal: float
    special: float
    exceptional: float
    table: str
    page: int


@dataclass(frozen=True, slots=True)
class GroupedVariableGammaFactors:
    normal: float
    special: float
    exceptional: float
    table: str
    page: int


@dataclass(frozen=True, slots=True)
class CombinationFactors:
    category: NBR8681VariablePsiCategory
    psi_0: float
    psi_1: float
    psi_2: float
    table: str
    page: int


PERMANENT_FACTORS = (
    PermanentFactors(
        NBR8681PermanentCategory.STEEL_SELF_WEIGHT_AND_EQUIPMENT,
        1.25,
        1.0,
        1.15,
        1.0,
        1.10,
        1.0,
        "Tabela 1",
        14,
    ),
    PermanentFactors(
        NBR8681PermanentCategory.PRECAST_WOOD_INDUSTRIALIZED,
        1.30,
        1.0,
        1.20,
        1.0,
        1.15,
        1.0,
        "Tabela 1",
        14,
    ),
    PermanentFactors(
        NBR8681PermanentCategory.CAST_IN_PLACE,
        1.35,
        1.0,
        1.25,
        1.0,
        1.15,
        1.0,
        "Tabela 1",
        14,
    ),
    PermanentFactors(
        NBR8681PermanentCategory.INDUSTRIALIZED_WITH_IN_LOCO_ADDITION,
        1.40,
        1.0,
        1.30,
        1.0,
        1.20,
        1.0,
        "Tabela 1",
        14,
    ),
    PermanentFactors(
        NBR8681PermanentCategory.GENERAL_CONSTRUCTION_ELEMENTS,
        1.50,
        1.0,
        1.40,
        1.0,
        1.30,
        1.0,
        "Tabela 1",
        14,
    ),
    PermanentFactors(
        NBR8681PermanentCategory.DIRECT_PERMANENT_GROUPED,
        1.35,
        1.0,
        1.25,
        1.0,
        1.15,
        1.0,
        "Tabela 2",
        14,
    ),
    PermanentFactors(
        NBR8681PermanentCategory.PRESTRESSING,
        1.20,
        0.90,
        1.20,
        0.90,
        1.20,
        0.90,
        "Tabela 3",
        15,
    ),
    PermanentFactors(
        NBR8681PermanentCategory.SETTLEMENT_AND_SHRINKAGE,
        1.20,
        0.0,
        1.20,
        0.0,
        0.0,
        0.0,
        "Tabela 3",
        15,
    ),
)


VARIABLE_GAMMA_FACTORS_SEPARATE = (
    VariableGammaFactors(
        NBR8681VariableGammaCategory.TRUNCATED,
        1.20,
        1.10,
        1.0,
        "Tabela 4",
        15,
    ),
    VariableGammaFactors(
        NBR8681VariableGammaCategory.ATMOSPHERIC_TEMPERATURE,
        1.20,
        1.0,
        1.0,
        "Tabela 4",
        15,
    ),
    VariableGammaFactors(
        NBR8681VariableGammaCategory.WIND,
        1.40,
        1.20,
        1.0,
        "Tabela 4",
        15,
    ),
    VariableGammaFactors(
        NBR8681VariableGammaCategory.OTHER,
        1.50,
        1.30,
        1.0,
        "Tabela 4",
        15,
    ),
)


GROUPED_VARIABLE_GAMMA_FACTORS = GroupedVariableGammaFactors(
    normal=1.50,
    special=1.30,
    exceptional=1.0,
    table="Tabela 5",
    page=16,
)


COMBINATION_FACTORS = (
    CombinationFactors(
        NBR8681VariablePsiCategory.RESIDENTIAL_RESTRICTED_ACCESS,
        0.5,
        0.4,
        0.3,
        "Tabela 6",
        16,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.COMMERCIAL_OFFICE_PUBLIC_ACCESS,
        0.7,
        0.6,
        0.4,
        "Tabela 6",
        16,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.STORAGE_WORKSHOP_GARAGE_ROOF,
        0.8,
        0.7,
        0.6,
        "Tabela 6",
        16,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.WIND,
        0.6,
        0.3,
        0.0,
        "Tabela 6",
        16,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.ATMOSPHERIC_TEMPERATURE,
        0.6,
        0.5,
        0.3,
        "Tabela 6",
        16,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.PEDESTRIAN_BRIDGE,
        0.6,
        0.4,
        0.3,
        "Tabela 6",
        17,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.ROAD_BRIDGE,
        0.7,
        0.5,
        0.3,
        "Tabela 6",
        17,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.RAILWAY_BRIDGE,
        1.0,
        1.0,
        0.6,
        "Tabela 6",
        17,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.CRANE_RUNWAY_BEAM,
        1.0,
        0.8,
        0.5,
        "Tabela 6",
        17,
    ),
    CombinationFactors(
        NBR8681VariablePsiCategory.SILO_OR_RESERVOIR,
        1.0,
        1.0,
        1.0,
        "Tabela 6, nota d",
        17,
    ),
)


EXCEPTIONAL_ACTION_FACTOR = 1.0
FIRE_PSI_2_REDUCTION = 0.7
SERVICE_PERMANENT_FACTOR = 1.0


def category_kind(
    category: (
        NBR8681PermanentCategory | NBR8681VariableClassification | NBR8681ExceptionalCategory
    ),
) -> ActionKind:
    if isinstance(category, NBR8681VariableClassification):
        return ActionKind.VARIABLE
    if isinstance(category, NBR8681ExceptionalCategory):
        return ActionKind.EXCEPTIONAL
    if category in {
        NBR8681PermanentCategory.PRESTRESSING,
        NBR8681PermanentCategory.SETTLEMENT_AND_SHRINKAGE,
    }:
        return ActionKind.PERMANENT_INDIRECT
    return ActionKind.PERMANENT_DIRECT


def _reference(item: str, page: int | None = None) -> NormativeReference:
    return NormativeReference(
        standard="ABNT NBR 8681",
        item=item,
        edition="2025",
        page=page,
        review_status="SOURCE_COPY_VERIFIED_DECISION_PENDING",
    )


def _permanent_values(
    factors: PermanentFactors,
    family: CombinationFamily,
) -> tuple[float, float]:
    if family is CombinationFamily.ULTIMATE_NORMAL:
        return factors.normal_unfavorable, factors.normal_favorable
    if family in {
        CombinationFamily.ULTIMATE_SPECIAL,
        CombinationFamily.ULTIMATE_CONSTRUCTION,
    }:
        return factors.special_unfavorable, factors.special_favorable
    if family is CombinationFamily.ULTIMATE_EXCEPTIONAL:
        return factors.exceptional_unfavorable, factors.exceptional_favorable
    return SERVICE_PERMANENT_FACTOR, SERVICE_PERMANENT_FACTOR


def _separate_gamma_factors(
    category: NBR8681VariableGammaCategory,
) -> VariableGammaFactors:
    for factors in VARIABLE_GAMMA_FACTORS_SEPARATE:
        if factors.category is category:
            return factors
    raise ValueError(f"Categoria sem gamma_q: {category.value}.")


def _variable_gamma(
    classification: NBR8681VariableClassification,
    family: CombinationFamily,
    grouping: ActionGrouping,
    grouped_temperature_treatment: GroupedAtmosphericTemperatureTreatment,
) -> tuple[float, str, int]:
    if family in {
        CombinationFamily.SERVICE_RARE,
        CombinationFamily.SERVICE_FREQUENT,
        CombinationFamily.SERVICE_QUASI_PERMANENT,
    }:
        psi = _psi_factors(classification.psi_category)
        return 1.0, psi.table, psi.page
    factors: VariableGammaFactors | GroupedVariableGammaFactors
    keep_temperature_separate = (
        grouping is ActionGrouping.GROUPED
        and classification.gamma_category is NBR8681VariableGammaCategory.ATMOSPHERIC_TEMPERATURE
        and grouped_temperature_treatment is GroupedAtmosphericTemperatureTreatment.KEEP_SEPARATE
    )
    if grouping is ActionGrouping.GROUPED and not keep_temperature_separate:
        factors = GROUPED_VARIABLE_GAMMA_FACTORS
    else:
        factors = _separate_gamma_factors(classification.gamma_category)
    if family is CombinationFamily.ULTIMATE_NORMAL:
        return factors.normal, factors.table, factors.page
    if family in {
        CombinationFamily.ULTIMATE_SPECIAL,
        CombinationFamily.ULTIMATE_CONSTRUCTION,
    }:
        return factors.special, factors.table, factors.page
    return factors.exceptional, factors.table, factors.page


def _psi_factors(category: NBR8681VariablePsiCategory) -> CombinationFactors:
    for factors in COMBINATION_FACTORS:
        if factors.category is category:
            return factors
    raise ValueError(f"Categoria sem psi: {category.value}.")


def _variable_roles(
    *,
    family: CombinationFamily,
    gamma: float,
    psi: CombinationFactors,
    effective_accompanying: EffectiveAccompanyingFactor,
    fire_psi_2_treatment: FirePsi2Treatment,
) -> tuple[tuple[TermRole, float], ...]:
    if family is CombinationFamily.SERVICE_QUASI_PERMANENT:
        return ((TermRole.ACCOMPANYING_VARIABLE, psi.psi_2),)
    if family is CombinationFamily.SERVICE_FREQUENT:
        return (
            (TermRole.LEADING_VARIABLE, psi.psi_1),
            (TermRole.ACCOMPANYING_VARIABLE, psi.psi_2),
        )
    if family is CombinationFamily.SERVICE_RARE:
        return (
            (TermRole.LEADING_VARIABLE, 1.0),
            (TermRole.ACCOMPANYING_VARIABLE, psi.psi_1),
        )
    if family is CombinationFamily.ULTIMATE_EXCEPTIONAL:
        effective = (
            psi.psi_0 if effective_accompanying is EffectiveAccompanyingFactor.PSI_0 else psi.psi_2
        )
        if fire_psi_2_treatment is FirePsi2Treatment.ADOPT_REDUCTION:
            effective *= FIRE_PSI_2_REDUCTION
        return ((TermRole.ACCOMPANYING_VARIABLE, gamma * effective),)
    effective = (
        psi.psi_0
        if family is CombinationFamily.ULTIMATE_NORMAL
        or effective_accompanying is EffectiveAccompanyingFactor.PSI_0
        else psi.psi_2
    )
    return (
        (TermRole.LEADING_VARIABLE, gamma),
        (TermRole.ACCOMPANYING_VARIABLE, gamma * effective),
    )


def _variable_reference(
    *,
    family: CombinationFamily,
    role: TermRole,
    gamma_table: str,
    gamma_page: int,
    psi: CombinationFactors,
    fire_psi_2_treatment: FirePsi2Treatment,
) -> NormativeReference:
    if family is CombinationFamily.SERVICE_QUASI_PERMANENT:
        return _reference(f"5.1.5.2, {psi.table}", psi.page)
    if family is CombinationFamily.SERVICE_FREQUENT:
        return _reference(f"5.1.5.3, {psi.table}", psi.page)
    if family is CombinationFamily.SERVICE_RARE:
        return _reference(f"5.1.5.4, {psi.table}", psi.page)
    family_item = {
        CombinationFamily.ULTIMATE_NORMAL: "5.1.3.1",
        CombinationFamily.ULTIMATE_SPECIAL: "5.1.3.2",
        CombinationFamily.ULTIMATE_CONSTRUCTION: "5.1.3.2",
        CombinationFamily.ULTIMATE_EXCEPTIONAL: "5.1.3.3",
    }[family]
    items = f"{family_item}; 5.1.4.2, {gamma_table} (p. {gamma_page})"
    if role is TermRole.ACCOMPANYING_VARIABLE:
        items += f"; 5.1.4.4, {psi.table} (p. {psi.page})"
        if (
            family is CombinationFamily.ULTIMATE_EXCEPTIONAL
            and fire_psi_2_treatment is FirePsi2Treatment.ADOPT_REDUCTION
        ):
            items += ", nota c"
    return _reference(items)


def build_pending_nbr8681_2025_rule_set(
    *,
    grouping: ActionGrouping,
    variable_classifications: tuple[NBR8681VariableClassification, ...],
    effective_accompanying: EffectiveAccompanyingFactor,
    grouped_temperature_treatment: GroupedAtmosphericTemperatureTreatment = (
        GroupedAtmosphericTemperatureTreatment.KEEP_SEPARATE
    ),
    fire_psi_2_treatment: FirePsi2Treatment = FirePsi2Treatment.NOT_APPLICABLE,
) -> CombinationRuleSet:
    """Monta regras bloqueadas até a decisão normativa ND-001."""

    if not variable_classifications:
        raise ValueError("Informe ao menos uma classificação de ação variável.")
    if len({item.category_id for item in variable_classifications}) != len(
        variable_classifications
    ):
        raise ValueError("Há classificação de ação variável duplicada.")
    if (
        fire_psi_2_treatment is FirePsi2Treatment.ADOPT_REDUCTION
        and effective_accompanying is not EffectiveAccompanyingFactor.PSI_2_FOR_VERY_SHORT_ACTION
    ):
        raise ValueError("A redução de incêndio somente pode incidir sobre psi_2.")

    families = tuple(CombinationFamily)
    rules: list[FactorRule] = []
    allowed_permanents = tuple(
        factors
        for factors in PERMANENT_FACTORS
        if (factors.category is NBR8681PermanentCategory.DIRECT_PERMANENT_GROUPED)
        == (grouping is ActionGrouping.GROUPED)
        or category_kind(factors.category) is ActionKind.PERMANENT_INDIRECT
    )
    for factors in allowed_permanents:
        for family in families:
            unfavorable, favorable = _permanent_values(factors, family)
            rules.append(
                FactorRule(
                    category_id=factors.category.value,
                    family=family,
                    role=TermRole.PERMANENT,
                    unfavorable_factor=unfavorable,
                    favorable_factor=favorable,
                    reference=_reference(
                        f"5.1.4.1, {factors.table}",
                        factors.page,
                    ),
                    reviewed=False,
                )
            )

    for classification in variable_classifications:
        psi = _psi_factors(classification.psi_category)
        for family in families:
            gamma, gamma_table, gamma_page = _variable_gamma(
                classification,
                family,
                grouping,
                grouped_temperature_treatment,
            )
            roles = _variable_roles(
                family=family,
                gamma=gamma,
                psi=psi,
                effective_accompanying=effective_accompanying,
                fire_psi_2_treatment=fire_psi_2_treatment,
            )
            for role, factor in roles:
                rules.append(
                    FactorRule(
                        category_id=classification.category_id,
                        family=family,
                        role=role,
                        unfavorable_factor=factor,
                        favorable_factor=0.0,
                        reference=_variable_reference(
                            family=family,
                            role=role,
                            gamma_table=gamma_table,
                            gamma_page=gamma_page,
                            psi=psi,
                            fire_psi_2_treatment=fire_psi_2_treatment,
                        ),
                        reviewed=False,
                    )
                )

    rules.append(
        FactorRule(
            category_id=NBR8681ExceptionalCategory.GENERAL.value,
            family=CombinationFamily.ULTIMATE_EXCEPTIONAL,
            role=TermRole.EXCEPTIONAL,
            unfavorable_factor=EXCEPTIONAL_ACTION_FACTOR,
            favorable_factor=0.0,
            reference=_reference("5.1.3.3 e 5.1.4.3", 13),
            reviewed=False,
        )
    )
    return CombinationRuleSet(
        rule_set_id=(
            f"NBR8681:2025:{grouping.value}:"
            f"{grouped_temperature_treatment.value}:"
            f"{effective_accompanying.value}:"
            f"{fire_psi_2_treatment.value}:PENDING"
        ),
        rules=tuple(rules),
        normative_decision_id="ND-001:NORMATIVE_REVIEW_REQUIRED",
    )
