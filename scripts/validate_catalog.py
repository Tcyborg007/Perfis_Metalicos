import argparse
import sys
from pathlib import Path

from perfis_metalicos.catalog import (
    CatalogValidationStatus,
    load_catalog_manifest,
    validate_catalog_workbook,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-validated", action="store_true")
    args = parser.parse_args()
    manifest_path = ROOT / "catalog" / "catalog_manifest.yaml"
    report = validate_catalog_workbook(ROOT / "perfis.xlsx", manifest_path)
    manifest = load_catalog_manifest(manifest_path)
    expected = manifest["workbook"]["status"]
    print(
        f"catalog_status={report.status.value} rows={report.row_count} "
        f"issues={len(report.issues)} sha256={report.workbook_sha256}"
    )
    if report.status.value != expected:
        print(f"Status calculado diverge do manifesto: esperado={expected}")
        return 1
    if (
        args.require_validated
        and report.status is not CatalogValidationStatus.VALIDATED_CATALOG_SOURCE
    ):
        print("Catálogo ainda não possui fonte validada.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
