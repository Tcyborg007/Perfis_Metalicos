import argparse
import json
from pathlib import Path

from perfis_metalicos.audit import build_reproducible_analysis_record

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "examples" / "reproducible_analysis_input.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "reproducible_analysis_record.json",
    )
    parser.add_argument("--commit", default="UNCOMMITTED")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    record = build_reproducible_analysis_record(
        payload,
        engine_version="0.1.0",
        commit=args.commit,
        catalog_path=ROOT / "perfis.xlsx",
        normative_manifest_path=ROOT / "norms" / "normative_manifest.yaml",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(record.canonical_json() + "\n", encoding="utf-8")
    print(
        f"record={args.output} input_sha256={record.input_sha256} "
        f"classification={record.classification}"
    )


if __name__ == "__main__":
    main()
