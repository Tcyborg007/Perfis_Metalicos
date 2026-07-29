import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "norms" / "normative_manifest.yaml"


def main() -> int:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("baseline_commit") != "ab68c099e53a1f26974fd2adcbe752b0d4c8a6ec":
        errors.append("commit-base normativo divergente")
    standards = data.get("standards")
    if not isinstance(standards, list) or not standards:
        errors.append("lista de normas ausente")
        standards = []
    required = {
        "identification",
        "edition",
        "current_status",
        "consulted_copy",
        "scope_used",
        "affected_functions",
        "existing_tests",
        "review",
    }
    for standard in standards:
        missing = sorted(required - set(standard))
        if missing:
            errors.append(
                f"{standard.get('key', '<sem chave>')}: campos ausentes: {', '.join(missing)}"
            )
        copy = standard.get("consulted_copy", {})
        if not copy.get("available") and (
            standard.get("current_status", {}).get("value")
            not in {"NORMATIVE_REVIEW_REQUIRED", "OUT_OF_SCOPE"}
        ):
            errors.append(
                f"{standard.get('key')}: fonte ausente sem bloqueio normativo"
            )
    if errors:
        print("\n".join(errors))
        return 1
    print(f"manifest_ok standards={len(standards)} status={data.get('manifest_status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
