import pytest

from perfis_metalicos.combinations import (
    COMBINATION_FACTORS,
    EXCEPTIONAL_ACTION_FACTOR,
    FIRE_PSI_2_REDUCTION,
    GROUPED_VARIABLE_GAMMA_FACTORS,
    PERMANENT_FACTORS,
    SERVICE_PERMANENT_FACTOR,
    VARIABLE_GAMMA_FACTORS_SEPARATE,
    ActionGrouping,
    CombinationFamily,
    EffectiveAccompanyingFactor,
    FirePsi2Treatment,
    GroupedAtmosphericTemperatureTreatment,
    NBR8681ExceptionalCategory,
    NBR8681PermanentCategory,
    NBR8681VariableClassification,
    NBR8681VariableGammaCategory,
    NBR8681VariablePsiCategory,
    TermRole,
    build_pending_nbr8681_2025_rule_set,
    category_kind,
    generate_combinations,
)
from perfis_metalicos.domain import (
    Action,
    ActionCategory,
    ActionKind,
    ActionMetadata,
    EffectNature,
    Length,
    LineLoad,
    UniformLineLoad,
)

COMMERCIAL = NBR8681VariableClassification(
    NBR8681VariableGammaCategory.OTHER,
    NBR8681VariablePsiCategory.COMMERCIAL_OFFICE_PUBLIC_ACCESS,
)
WIND = NBR8681VariableClassification(
    NBR8681VariableGammaCategory.WIND,
    NBR8681VariablePsiCategory.WIND,
)
TRUNCATED_RESIDENTIAL = NBR8681VariableClassification(
    NBR8681VariableGammaCategory.TRUNCATED,
    NBR8681VariablePsiCategory.RESIDENTIAL_RESTRICTED_ACCESS,
)
TEMPERATURE = NBR8681VariableClassification(
    NBR8681VariableGammaCategory.ATMOSPHERIC_TEMPERATURE,
    NBR8681VariablePsiCategory.ATMOSPHERIC_TEMPERATURE,
)
CLASSIFICATIONS = (COMMERCIAL, WIND, TRUNCATED_RESIDENTIAL)


def rule_set(grouping=ActionGrouping.SEPARATE):
    return build_pending_nbr8681_2025_rule_set(
        grouping=grouping,
        variable_classifications=CLASSIFICATIONS,
        effective_accompanying=EffectiveAccompanyingFactor.PSI_0,
    )


def find_rule(
    classification,
    family,
    role,
    grouping=ActionGrouping.SEPARATE,
):
    return next(
        rule
        for rule in rule_set(grouping).rules
        if rule.category_id == classification.category_id
        and rule.family is family
        and rule.role is role
    )


def test_all_transcribed_permanent_constants_have_source_and_boundaries():
    values = {
        item.category: (
            item.normal_unfavorable,
            item.normal_favorable,
            item.special_unfavorable,
            item.special_favorable,
            item.exceptional_unfavorable,
            item.exceptional_favorable,
        )
        for item in PERMANENT_FACTORS
    }
    assert values == {
        NBR8681PermanentCategory.STEEL_SELF_WEIGHT_AND_EQUIPMENT: (
            1.25,
            1.0,
            1.15,
            1.0,
            1.10,
            1.0,
        ),
        NBR8681PermanentCategory.PRECAST_WOOD_INDUSTRIALIZED: (
            1.30,
            1.0,
            1.20,
            1.0,
            1.15,
            1.0,
        ),
        NBR8681PermanentCategory.CAST_IN_PLACE: (
            1.35,
            1.0,
            1.25,
            1.0,
            1.15,
            1.0,
        ),
        NBR8681PermanentCategory.INDUSTRIALIZED_WITH_IN_LOCO_ADDITION: (
            1.40,
            1.0,
            1.30,
            1.0,
            1.20,
            1.0,
        ),
        NBR8681PermanentCategory.GENERAL_CONSTRUCTION_ELEMENTS: (
            1.50,
            1.0,
            1.40,
            1.0,
            1.30,
            1.0,
        ),
        NBR8681PermanentCategory.DIRECT_PERMANENT_GROUPED: (
            1.35,
            1.0,
            1.25,
            1.0,
            1.15,
            1.0,
        ),
        NBR8681PermanentCategory.PRESTRESSING: (
            1.20,
            0.90,
            1.20,
            0.90,
            1.20,
            0.90,
        ),
        NBR8681PermanentCategory.SETTLEMENT_AND_SHRINKAGE: (
            1.20,
            0.0,
            1.20,
            0.0,
            0.0,
            0.0,
        ),
    }
    assert all(item.table and item.page in {14, 15} for item in PERMANENT_FACTORS)
    assert SERVICE_PERMANENT_FACTOR == EXCEPTIONAL_ACTION_FACTOR == 1.0


def test_tables_4_and_5_are_transcribed_once_and_completely():
    separate = {
        item.category: (item.normal, item.special, item.exceptional)
        for item in VARIABLE_GAMMA_FACTORS_SEPARATE
    }
    assert separate == {
        NBR8681VariableGammaCategory.TRUNCATED: (1.2, 1.1, 1.0),
        NBR8681VariableGammaCategory.ATMOSPHERIC_TEMPERATURE: (
            1.2,
            1.0,
            1.0,
        ),
        NBR8681VariableGammaCategory.WIND: (1.4, 1.2, 1.0),
        NBR8681VariableGammaCategory.OTHER: (1.5, 1.3, 1.0),
    }
    assert (
        GROUPED_VARIABLE_GAMMA_FACTORS.normal,
        GROUPED_VARIABLE_GAMMA_FACTORS.special,
        GROUPED_VARIABLE_GAMMA_FACTORS.exceptional,
    ) == (1.5, 1.3, 1.0)


def test_table_6_is_transcribed_once_and_completely():
    values = {item.category: (item.psi_0, item.psi_1, item.psi_2) for item in COMBINATION_FACTORS}
    assert values == {
        NBR8681VariablePsiCategory.RESIDENTIAL_RESTRICTED_ACCESS: (
            0.5,
            0.4,
            0.3,
        ),
        NBR8681VariablePsiCategory.COMMERCIAL_OFFICE_PUBLIC_ACCESS: (
            0.7,
            0.6,
            0.4,
        ),
        NBR8681VariablePsiCategory.STORAGE_WORKSHOP_GARAGE_ROOF: (
            0.8,
            0.7,
            0.6,
        ),
        NBR8681VariablePsiCategory.WIND: (0.6, 0.3, 0.0),
        NBR8681VariablePsiCategory.ATMOSPHERIC_TEMPERATURE: (
            0.6,
            0.5,
            0.3,
        ),
        NBR8681VariablePsiCategory.PEDESTRIAN_BRIDGE: (0.6, 0.4, 0.3),
        NBR8681VariablePsiCategory.ROAD_BRIDGE: (0.7, 0.5, 0.3),
        NBR8681VariablePsiCategory.RAILWAY_BRIDGE: (1.0, 1.0, 0.6),
        NBR8681VariablePsiCategory.CRANE_RUNWAY_BEAM: (1.0, 0.8, 0.5),
        NBR8681VariablePsiCategory.SILO_OR_RESERVOIR: (1.0, 1.0, 1.0),
    }
    assert FIRE_PSI_2_REDUCTION == 0.7


def test_variable_classification_keeps_gamma_and_psi_dimensions_separate():
    assert TRUNCATED_RESIDENTIAL.category_id == ("GAMMA_Q_TRUNCATED::PSI_USE_RESIDENTIAL")
    with pytest.raises(ValueError, match="exige"):
        NBR8681VariableClassification(
            NBR8681VariableGammaCategory.WIND,
            NBR8681VariablePsiCategory.COMMERCIAL_OFFICE_PUBLIC_ACCESS,
        )
    with pytest.raises(ValueError, match="PSI_WIND"):
        NBR8681VariableClassification(
            NBR8681VariableGammaCategory.OTHER,
            NBR8681VariablePsiCategory.WIND,
        )


def test_ultimate_and_service_roles_use_the_correct_products():
    assert (
        find_rule(
            COMMERCIAL,
            CombinationFamily.ULTIMATE_NORMAL,
            TermRole.LEADING_VARIABLE,
        ).unfavorable_factor
        == 1.5
    )
    assert find_rule(
        COMMERCIAL,
        CombinationFamily.ULTIMATE_NORMAL,
        TermRole.ACCOMPANYING_VARIABLE,
    ).unfavorable_factor == pytest.approx(1.5 * 0.7)
    assert (
        find_rule(
            COMMERCIAL,
            CombinationFamily.SERVICE_RARE,
            TermRole.LEADING_VARIABLE,
        ).unfavorable_factor
        == 1.0
    )
    assert (
        find_rule(
            COMMERCIAL,
            CombinationFamily.SERVICE_RARE,
            TermRole.ACCOMPANYING_VARIABLE,
        ).unfavorable_factor
        == 0.6
    )
    assert (
        find_rule(
            COMMERCIAL,
            CombinationFamily.SERVICE_FREQUENT,
            TermRole.LEADING_VARIABLE,
        ).unfavorable_factor
        == 0.6
    )
    assert (
        find_rule(
            COMMERCIAL,
            CombinationFamily.SERVICE_FREQUENT,
            TermRole.ACCOMPANYING_VARIABLE,
        ).unfavorable_factor
        == 0.4
    )
    assert (
        find_rule(
            COMMERCIAL,
            CombinationFamily.SERVICE_QUASI_PERMANENT,
            TermRole.ACCOMPANYING_VARIABLE,
        ).unfavorable_factor
        == 0.4
    )


def test_grouped_option_changes_gamma_and_permanent_category_set():
    wind_separate = find_rule(
        WIND,
        CombinationFamily.ULTIMATE_NORMAL,
        TermRole.LEADING_VARIABLE,
    )
    wind_grouped = find_rule(
        WIND,
        CombinationFamily.ULTIMATE_NORMAL,
        TermRole.LEADING_VARIABLE,
        grouping=ActionGrouping.GROUPED,
    )
    assert wind_separate.unfavorable_factor == 1.4
    assert wind_grouped.unfavorable_factor == 1.5
    grouped_categories = {rule.category_id for rule in rule_set(ActionGrouping.GROUPED).rules}
    assert NBR8681PermanentCategory.DIRECT_PERMANENT_GROUPED.value in grouped_categories
    assert NBR8681PermanentCategory.STEEL_SELF_WEIGHT_AND_EQUIPMENT.value not in grouped_categories


def test_grouped_temperature_can_remain_separate_as_table_5_allows():
    separate_temperature = build_pending_nbr8681_2025_rule_set(
        grouping=ActionGrouping.GROUPED,
        variable_classifications=(TEMPERATURE,),
        effective_accompanying=EffectiveAccompanyingFactor.PSI_0,
        grouped_temperature_treatment=(GroupedAtmosphericTemperatureTreatment.KEEP_SEPARATE),
    )
    grouped_temperature = build_pending_nbr8681_2025_rule_set(
        grouping=ActionGrouping.GROUPED,
        variable_classifications=(TEMPERATURE,),
        effective_accompanying=EffectiveAccompanyingFactor.PSI_0,
        grouped_temperature_treatment=(
            GroupedAtmosphericTemperatureTreatment.GROUP_WITH_VARIABLE_ACTIONS
        ),
    )

    def leading_gamma(rules):
        return next(
            item.unfavorable_factor
            for item in rules.rules
            if item.category_id == TEMPERATURE.category_id
            and item.family is CombinationFamily.ULTIMATE_NORMAL
            and item.role is TermRole.LEADING_VARIABLE
        )

    assert leading_gamma(separate_temperature) == 1.2
    assert leading_gamma(grouped_temperature) == 1.5


def test_very_short_special_action_uses_psi_2_for_accompanying_action():
    rules = build_pending_nbr8681_2025_rule_set(
        grouping=ActionGrouping.SEPARATE,
        variable_classifications=(TRUNCATED_RESIDENTIAL,),
        effective_accompanying=(EffectiveAccompanyingFactor.PSI_2_FOR_VERY_SHORT_ACTION),
    )
    rule = next(
        item
        for item in rules.rules
        if item.category_id == TRUNCATED_RESIDENTIAL.category_id
        and item.family is CombinationFamily.ULTIMATE_SPECIAL
        and item.role is TermRole.ACCOMPANYING_VARIABLE
    )
    assert rule.unfavorable_factor == pytest.approx(1.1 * 0.3)


def test_fire_option_reduces_only_psi_2_in_exceptional_combination():
    rules = build_pending_nbr8681_2025_rule_set(
        grouping=ActionGrouping.SEPARATE,
        variable_classifications=(COMMERCIAL,),
        effective_accompanying=(EffectiveAccompanyingFactor.PSI_2_FOR_VERY_SHORT_ACTION),
        fire_psi_2_treatment=FirePsi2Treatment.ADOPT_REDUCTION,
    )
    companion = next(
        item
        for item in rules.rules
        if item.category_id == COMMERCIAL.category_id
        and item.family is CombinationFamily.ULTIMATE_EXCEPTIONAL
        and item.role is TermRole.ACCOMPANYING_VARIABLE
    )
    assert companion.unfavorable_factor == pytest.approx(1.0 * 0.4 * 0.7)
    with pytest.raises(ValueError, match="somente pode incidir"):
        build_pending_nbr8681_2025_rule_set(
            grouping=ActionGrouping.SEPARATE,
            variable_classifications=(COMMERCIAL,),
            effective_accompanying=EffectiveAccompanyingFactor.PSI_0,
            fire_psi_2_treatment=FirePsi2Treatment.ADOPT_REDUCTION,
        )


def test_category_kinds_and_pending_decision_block_generation():
    assert (
        category_kind(NBR8681PermanentCategory.STEEL_SELF_WEIGHT_AND_EQUIPMENT)
        is ActionKind.PERMANENT_DIRECT
    )
    assert category_kind(NBR8681PermanentCategory.PRESTRESSING) is ActionKind.PERMANENT_INDIRECT
    assert category_kind(WIND) is ActionKind.VARIABLE
    assert category_kind(NBR8681ExceptionalCategory.GENERAL) is ActionKind.EXCEPTIONAL
    action = Action(
        action_id="Q",
        name="Uso e ocupação",
        category=ActionCategory(
            COMMERCIAL.category_id,
            category_kind(COMMERCIAL),
            find_rule(
                COMMERCIAL,
                CombinationFamily.ULTIMATE_NORMAL,
                TermRole.LEADING_VARIABLE,
            ).reference,
        ),
        loads=(UniformLineLoad(Length(0.0), Length(500.0), LineLoad(0.01)),),
        metadata=ActionMetadata(origin="Entrada de teste"),
        effect_nature=EffectNature.UNFAVORABLE,
    )
    with pytest.raises(ValueError, match="requer revisão normativa"):
        generate_combinations(
            (action,),
            CombinationFamily.ULTIMATE_NORMAL,
            rule_set(),
        )
