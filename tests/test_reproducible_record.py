import json
from pathlib import Path

from perfis_metalicos.audit import (
    build_reproducible_analysis_record,
    canonical_json,
    sha256_text,
)

ROOT = Path(__file__).resolve().parents[1]


def payload():
    return json.loads(
        (ROOT / "examples" / "reproducible_analysis_input.json").read_text(
            encoding="utf-8"
        )
    )


def build(data):
    return build_reproducible_analysis_record(
        data,
        engine_version="0.1.0",
        commit="TEST-COMMIT",
        catalog_path=ROOT / "perfis.xlsx",
        normative_manifest_path=ROOT / "norms" / "normative_manifest.yaml",
    )


def test_same_immutable_input_generates_identical_record():
    first = build(payload())
    second = build(payload())
    assert first.canonical_json() == second.canonical_json()
    assert first.input_sha256 == sha256_text(canonical_json(payload()))


def test_any_input_change_changes_hash_and_result():
    original = payload()
    changed = payload()
    changed["loads"][1]["force_kN"] = 13.0
    first = build(original)
    second = build(changed)
    assert first.input_sha256 != second.input_sha256
    assert first.analysis_result != second.analysis_result


def test_record_never_claims_approval_with_known_pending_items():
    record = build(payload())
    assert record.classification == "NÃO VALIDADO"
    assert "INVALID_CATALOG_DATA" in record.pending_items
    assert record.catalog_sha256 == (
        "EB95CEA376935EF62C8B9C311E0BB8BD72A80EE65BC69811E87CB2C8D2C08001"
    )

