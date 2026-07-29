"""Validação rastreável do catálogo de perfis."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


class CatalogValidationStatus(Enum):
    VALIDATED_CATALOG_SOURCE = "VALIDATED_CATALOG_SOURCE"
    UNVALIDATED_CATALOG_SOURCE = "UNVALIDATED_CATALOG_SOURCE"
    INVALID_CATALOG_DATA = "INVALID_CATALOG_DATA"


@dataclass(frozen=True, slots=True)
class CatalogIssue:
    family: str
    row: int | None
    designation: str | None
    check: str
    message: str
    blocking: bool = True


@dataclass(frozen=True, slots=True)
class CatalogValidationReport:
    status: CatalogValidationStatus
    workbook_sha256: str
    row_count: int
    family_count: int
    issues: tuple[CatalogIssue, ...]
    metadata_complete: bool

    @property
    def blocking_issues(self) -> tuple[CatalogIssue, ...]:
        return tuple(issue for issue in self.issues if issue.blocking)


REQUIRED_COLUMNS = (
    "Bitola (mm x kg/m)",
    "Massa Linear (kg/m)",
    "d (mm)",
    "bf (mm)",
    "tw (mm)",
    "tf (mm)",
    "h (mm)",
    "d' (mm)",
    "Área (cm2)",
    "Ix (cm4)",
    "Wx (cm3)",
    "Zx (cm3)",
    "Iy (cm4)",
    "ry (cm)",
    "It (cm4)",
    "Cw (cm6)",
)
POSITIVE_COLUMNS = tuple(column for column in REQUIRED_COLUMNS if column != "Bitola (mm x kg/m)")
METADATA_FIELDS = (
    "manufacturer",
    "catalog",
    "edition",
    "page",
    "origin",
    "source_hash",
    "source_date",
    "tolerances",
    "reviewer",
    "review_date",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_catalog_manifest(path: Path) -> Mapping[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        raise ValueError("Manifesto de catálogo ausente ou com versão incompatível.")
    return data


def _relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1e-12)


def _append_consistency_issues(
    issues: list[CatalogIssue],
    family: str,
    row_number: int,
    row: pd.Series,
    *,
    relative_tolerance: float,
) -> None:
    designation = str(row["Bitola (mm x kg/m)"])
    d_cm = float(row["d (mm)"]) / 10.0
    area = float(row["Área (cm2)"])
    iy = float(row["Iy (cm4)"])
    ry = float(row["ry (cm)"])
    ix = float(row["Ix (cm4)"])
    wx = float(row["Wx (cm3)"])
    zx = float(row["Zx (cm3)"])
    mass = float(row["Massa Linear (kg/m)"])
    d_clear = float(row["d' (mm)"])

    checks = (
        (
            "D_CLEAR_LT_D",
            d_clear < float(row["d (mm)"]),
            "d' deve ser menor que d.",
        ),
        (
            "MASS_FROM_AREA",
            _relative_error(mass, area * 0.785) <= relative_tolerance,
            "Massa linear incompatível com A·0,785.",
        ),
        (
            "RY_FROM_IY_AREA",
            _relative_error(ry**2, iy / area) <= relative_tolerance,
            "ry² incompatível com Iy/A.",
        ),
        (
            "WX_FROM_IX",
            _relative_error(wx, ix / (d_cm / 2.0)) <= relative_tolerance,
            "Wx incompatível com Ix/(d/2) para a seção simétrica declarada.",
        ),
        (
            "ZX_GE_WX",
            zx + 1e-12 >= wx,
            "Zx não pode ser menor que Wx.",
        ),
    )
    for check, passed, message in checks:
        if not passed:
            issues.append(
                CatalogIssue(
                    family=family,
                    row=row_number,
                    designation=designation,
                    check=check,
                    message=message,
                )
            )


def validate_catalog_workbook(
    workbook_path: Path,
    manifest_path: Path,
    *,
    relative_tolerance: float = 0.03,
) -> CatalogValidationReport:
    if not math.isfinite(relative_tolerance) or relative_tolerance <= 0:
        raise ValueError("A tolerância relativa deve ser positiva e finita.")
    workbook_path = workbook_path.resolve()
    manifest = load_catalog_manifest(manifest_path.resolve())
    workbook_hash = sha256_file(workbook_path)
    issues: list[CatalogIssue] = []
    declared_hash = str(manifest.get("workbook", {}).get("sha256") or "").upper()
    if declared_hash != workbook_hash:
        issues.append(
            CatalogIssue(
                family="*",
                row=None,
                designation=None,
                check="WORKBOOK_HASH",
                message="O hash do arquivo não coincide com o manifesto.",
            )
        )

    workbook = pd.read_excel(workbook_path, sheet_name=None)
    declared_families = manifest.get("families", {})
    metadata_complete = True
    row_count = 0
    for family, frame in workbook.items():
        family_metadata = declared_families.get(family)
        if not isinstance(family_metadata, dict):
            metadata_complete = False
            issues.append(
                CatalogIssue(
                    family=family,
                    row=None,
                    designation=None,
                    check="FAMILY_METADATA",
                    message="Família ausente do manifesto.",
                )
            )
        elif any(not family_metadata.get(field) for field in METADATA_FIELDS):
            metadata_complete = False
            issues.append(
                CatalogIssue(
                    family=family,
                    row=None,
                    designation=None,
                    check="UNVALIDATED_CATALOG_SOURCE",
                    message="Metadados oficiais e revisão da família estão incompletos.",
                )
            )

        missing = tuple(column for column in REQUIRED_COLUMNS if column not in frame.columns)
        if missing:
            issues.append(
                CatalogIssue(
                    family=family,
                    row=None,
                    designation=None,
                    check="REQUIRED_COLUMNS",
                    message="Colunas obrigatórias ausentes: " + ", ".join(missing),
                )
            )
            continue

        duplicates = frame["Bitola (mm x kg/m)"].duplicated(keep=False)
        for index, row in frame.loc[duplicates].iterrows():
            issues.append(
                CatalogIssue(
                    family=family,
                    row=int(index) + 2,
                    designation=str(row["Bitola (mm x kg/m)"]),
                    check="DUPLICATE_DESIGNATION",
                    message="Designação duplicada dentro da família.",
                )
            )

        for index, row in frame.iterrows():
            row_count += 1
            designation = str(row["Bitola (mm x kg/m)"])
            for column in POSITIVE_COLUMNS:
                value = row[column]
                if pd.isna(value) or not math.isfinite(float(value)) or float(value) <= 0:
                    issues.append(
                        CatalogIssue(
                            family=family,
                            row=int(index) + 2,
                            designation=designation,
                            check="POSITIVE_VALUE",
                            message=f"{column} deve ser positivo e finito.",
                        )
                    )
            if not any(
                issue.family == family
                and issue.row == int(index) + 2
                and issue.check == "POSITIVE_VALUE"
                for issue in issues
            ):
                _append_consistency_issues(
                    issues,
                    family,
                    int(index) + 2,
                    row,
                    relative_tolerance=relative_tolerance,
                )

    has_data_error = any(
        issue.check != "UNVALIDATED_CATALOG_SOURCE" for issue in issues
    )
    if has_data_error:
        status = CatalogValidationStatus.INVALID_CATALOG_DATA
    elif not metadata_complete:
        status = CatalogValidationStatus.UNVALIDATED_CATALOG_SOURCE
    else:
        status = CatalogValidationStatus.VALIDATED_CATALOG_SOURCE
    return CatalogValidationReport(
        status=status,
        workbook_sha256=workbook_hash,
        row_count=row_count,
        family_count=len(workbook),
        issues=tuple(issues),
        metadata_complete=metadata_complete,
    )

