"""Gerador genérico de combinações dirigido por regras externas.

Este módulo não contém coeficientes normativos. Uma combinação somente é gerada
quando todas as regras possuem fonte e foram marcadas como revisadas.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from itertools import product

from perfis_metalicos.domain.actions import (
    Action,
    ActionKind,
    EffectNature,
    Load,
)
from perfis_metalicos.domain.status import NormativeReference


class CombinationFamily(Enum):
    ULTIMATE_NORMAL = "ULTIMATE_NORMAL"
    ULTIMATE_SPECIAL = "ULTIMATE_SPECIAL"
    ULTIMATE_CONSTRUCTION = "ULTIMATE_CONSTRUCTION"
    ULTIMATE_EXCEPTIONAL = "ULTIMATE_EXCEPTIONAL"
    SERVICE_RARE = "SERVICE_RARE"
    SERVICE_FREQUENT = "SERVICE_FREQUENT"
    SERVICE_QUASI_PERMANENT = "SERVICE_QUASI_PERMANENT"


class TermRole(Enum):
    PERMANENT = "PERMANENT"
    LEADING_VARIABLE = "LEADING_VARIABLE"
    ACCOMPANYING_VARIABLE = "ACCOMPANYING_VARIABLE"
    EXCEPTIONAL = "EXCEPTIONAL"


@dataclass(frozen=True, slots=True)
class FactorRule:
    category_id: str
    family: CombinationFamily
    role: TermRole
    unfavorable_factor: float
    favorable_factor: float
    reference: NormativeReference
    reviewed: bool

    def __post_init__(self) -> None:
        if not self.category_id.strip():
            raise ValueError("category_id é obrigatório na regra.")
        for name, value in (
            ("unfavorable_factor", self.unfavorable_factor),
            ("favorable_factor", self.favorable_factor),
        ):
            if value < 0:
                raise ValueError(f"{name} não pode ser negativo.")

    def factors_for(self, nature: EffectNature) -> tuple[float, ...]:
        if nature is EffectNature.UNFAVORABLE:
            return (self.unfavorable_factor,)
        if nature is EffectNature.FAVORABLE:
            return (self.favorable_factor,)
        if self.unfavorable_factor == self.favorable_factor:
            return (self.unfavorable_factor,)
        return (self.unfavorable_factor, self.favorable_factor)


@dataclass(frozen=True, slots=True)
class CombinationRuleSet:
    rule_set_id: str
    rules: tuple[FactorRule, ...]
    normative_decision_id: str

    def __post_init__(self) -> None:
        if not self.rule_set_id.strip() or not self.normative_decision_id.strip():
            raise ValueError("A regra deve possuir identificação e decisão normativa.")
        keys = [(r.category_id, r.family, r.role) for r in self.rules]
        if len(keys) != len(set(keys)):
            raise ValueError("Há regras duplicadas para categoria, família e papel.")

    def rule_for(
        self,
        category_id: str,
        family: CombinationFamily,
        role: TermRole,
    ) -> FactorRule:
        for rule in self.rules:
            if (
                rule.category_id == category_id
                and rule.family is family
                and rule.role is role
            ):
                if not rule.reviewed:
                    raise ValueError(
                        f"Regra {category_id}/{family.value}/{role.value} requer revisão normativa."
                    )
                return rule
        raise ValueError(
            f"Categoria sem regra aplicável: {category_id}/{family.value}/{role.value}."
        )


@dataclass(frozen=True, slots=True)
class CombinationTerm:
    action: Action
    factor: float
    role: TermRole
    reference: NormativeReference

    @property
    def scaled_loads(self) -> tuple[Load, ...]:
        return tuple(load.scaled(self.factor) for load in self.action.loads)


@dataclass(frozen=True, slots=True)
class LoadCombination:
    combination_id: str
    family: CombinationFamily
    leading_action_id: str | None
    terms: tuple[CombinationTerm, ...]
    rule_set_id: str
    normative_decision_id: str

    @property
    def loads(self) -> tuple[Load, ...]:
        return tuple(load for term in self.terms for load in term.scaled_loads)

    @property
    def coefficients(self) -> tuple[tuple[str, float, str], ...]:
        return tuple(
            (term.action.action_id, term.factor, term.reference.item)
            for term in self.terms
        )


def _role_for(
    action: Action,
    family: CombinationFamily,
    leading_action_id: str | None,
) -> TermRole | None:
    if action.category.kind in {
        ActionKind.PERMANENT_DIRECT,
        ActionKind.PERMANENT_INDIRECT,
    }:
        return TermRole.PERMANENT
    if action.category.kind is ActionKind.EXCEPTIONAL:
        return (
            TermRole.EXCEPTIONAL
            if family is CombinationFamily.ULTIMATE_EXCEPTIONAL
            and action.action_id == leading_action_id
            else None
        )
    if action.category.kind is ActionKind.VARIABLE:
        return (
            TermRole.LEADING_VARIABLE
            if action.action_id == leading_action_id
            else TermRole.ACCOMPANYING_VARIABLE
        )
    return None


def _leaders_for(
    actions: tuple[Action, ...],
    family: CombinationFamily,
) -> tuple[str | None, ...]:
    if family is CombinationFamily.SERVICE_QUASI_PERMANENT:
        return (None,)
    if family is CombinationFamily.ULTIMATE_EXCEPTIONAL:
        leaders = tuple(
            action.action_id
            for action in actions
            if action.category.kind is ActionKind.EXCEPTIONAL
        )
        if not leaders:
            raise ValueError("Combinação excepcional exige ao menos uma ação excepcional.")
        return leaders
    leaders = tuple(
        action.action_id
        for action in actions
        if action.category.kind is ActionKind.VARIABLE
    )
    if not leaders:
        raise ValueError(f"{family.value} exige ao menos uma ação variável principal.")
    return leaders


def generate_combinations(
    actions: Iterable[Action],
    family: CombinationFamily,
    rule_set: CombinationRuleSet,
) -> tuple[LoadCombination, ...]:
    values = tuple(actions)
    if not values:
        raise ValueError("Ao menos uma ação é obrigatória.")
    action_ids = [action.action_id for action in values]
    if len(action_ids) != len(set(action_ids)):
        raise ValueError("action_id deve ser único.")

    combinations: list[LoadCombination] = []
    for leader_id in _leaders_for(values, family):
        action_rules: list[tuple[Action, TermRole, FactorRule]] = []
        for action in values:
            role = _role_for(action, family, leader_id)
            if role is None:
                continue
            rule = rule_set.rule_for(action.category.category_id, family, role)
            action_rules.append((action, role, rule))

        factor_options = [
            rule.factors_for(action.effect_nature)
            for action, _, rule in action_rules
        ]
        for variant_index, selected in enumerate(product(*factor_options), start=1):
            terms = tuple(
                CombinationTerm(
                    action=action,
                    factor=factor,
                    role=role,
                    reference=rule.reference,
                )
                for (action, role, rule), factor in zip(
                    action_rules, selected, strict=True
                )
            )
            leader_token = leader_id or "NO_LEADER"
            combinations.append(
                LoadCombination(
                    combination_id=(
                        f"{family.value}:{leader_token}:V{variant_index}"
                    ),
                    family=family,
                    leading_action_id=leader_id,
                    terms=terms,
                    rule_set_id=rule_set.rule_set_id,
                    normative_decision_id=rule_set.normative_decision_id,
                )
            )
    return tuple(combinations)

