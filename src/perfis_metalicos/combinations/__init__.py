"""Geradores de combinações dirigidos por regras controladas."""

from perfis_metalicos.combinations.generator import (
    CombinationFamily,
    CombinationRuleSet,
    FactorRule,
    LoadCombination,
    TermRole,
    generate_combinations,
)

__all__ = [
    "CombinationFamily",
    "CombinationRuleSet",
    "FactorRule",
    "LoadCombination",
    "TermRole",
    "generate_combinations",
]
