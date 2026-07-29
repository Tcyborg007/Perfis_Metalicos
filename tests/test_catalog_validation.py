from pathlib import Path

import pandas as pd
import pytest
import yaml

from perfis_metalicos.catalog import (
    CatalogValidationStatus,
    sha256_file,
    validate_catalog_workbook,
)


ROOT = Path(__file__).resolve().parents[1]


def valid_row(designation: str = "TEST 100 x 10") -> dict[str, float | str]:
    area = 12.7388535
    d_mm = 100.0
    ix = 500.0
    iy = 80.0
    return {
        "Bitola (mm x kg/m)": designation,
        "Massa Linear (kg/m)": area * 0.785,
        "d (mm)": d_mm,
        "bf (mm)": 80.0,
        "tw (mm)": 5.0,
        "tf (mm)": 7.0,
        "h (mm)": 86.0,
        "d' (mm)": 80.0,
        "Área (cm2)": area,
        "Ix (cm4)": ix,
        "Wx (cm3)": ix / (d_mm / 20.0),
        "rx (cm)": (ix / area) ** 0.5,
        "Zx (cm3)": 110.0,
        "Iy (cm4)": iy,
        "Wy (cm3)": 20.0,
        "ry (cm)": (iy / area) ** 0.5,
        "Zy (cm3)": 30.0,
        "rt (cm)": 2.0,
        "It (cm4)": 2.0,
        "Cw (cm6)": 1000.0,
    }


def write_manifest(path: Path, workbook: Path, *, complete: bool) -> None:
    value = "reviewed" if complete else None
    metadata = {
        field: value
        for field in (
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
    }
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "workbook": {"sha256": sha256_file(workbook)},
                "families": {"TEST": metadata},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_synthetic_valid_catalog_requires_complete_source_metadata(tmp_path):
    workbook = tmp_path / "profiles.xlsx"
    pd.DataFrame([valid_row()]).to_excel(workbook, sheet_name="TEST", index=False)
    manifest = tmp_path / "manifest.yaml"
    write_manifest(manifest, workbook, complete=False)
    report = validate_catalog_workbook(workbook, manifest)
    assert report.status is CatalogValidationStatus.UNVALIDATED_CATALOG_SOURCE
    assert report.row_count == 1


def test_synthetic_valid_catalog_can_be_validated_when_metadata_is_complete(tmp_path):
    workbook = tmp_path / "profiles.xlsx"
    pd.DataFrame([valid_row()]).to_excel(workbook, sheet_name="TEST", index=False)
    manifest = tmp_path / "manifest.yaml"
    write_manifest(manifest, workbook, complete=True)
    report = validate_catalog_workbook(workbook, manifest)
    assert report.status is CatalogValidationStatus.VALIDATED_CATALOG_SOURCE
    assert report.issues == ()


@pytest.mark.parametrize(
    ("field", "bad_value", "check"),
    (
        ("d' (mm)", 100.0, "D_CLEAR_LT_D"),
        ("Massa Linear (kg/m)", 20.0, "MASS_FROM_AREA"),
        ("ry (cm)", 8.0, "RY_FROM_IY_AREA"),
        ("Wx (cm3)", 20.0, "WX_FROM_IX"),
        ("Zx (cm3)", 50.0, "ZX_GE_WX"),
    ),
)
def test_each_required_consistency_check_is_blocking(tmp_path, field, bad_value, check):
    workbook = tmp_path / "profiles.xlsx"
    row = valid_row()
    row[field] = bad_value
    pd.DataFrame([row]).to_excel(workbook, sheet_name="TEST", index=False)
    manifest = tmp_path / "manifest.yaml"
    write_manifest(manifest, workbook, complete=True)
    report = validate_catalog_workbook(workbook, manifest)
    assert report.status is CatalogValidationStatus.INVALID_CATALOG_DATA
    assert any(issue.check == check for issue in report.issues)


def test_repository_catalog_hash_and_unvalidated_source_are_explicit():
    report = validate_catalog_workbook(
        ROOT / "perfis.xlsx",
        ROOT / "catalog" / "catalog_manifest.yaml",
    )
    assert report.workbook_sha256 == (
        "EB95CEA376935EF62C8B9C311E0BB8BD72A80EE65BC69811E87CB2C8D2C08001"
    )
    assert report.status in {
        CatalogValidationStatus.UNVALIDATED_CATALOG_SOURCE,
        CatalogValidationStatus.INVALID_CATALOG_DATA,
    }
    assert report.row_count == 560
    assert report.family_count == 4
    assert any(
        issue.check == "UNVALIDATED_CATALOG_SOURCE" for issue in report.issues
    )
    assert any(issue.check == "DUPLICATE_DESIGNATION" for issue in report.issues)
