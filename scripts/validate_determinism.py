import hashlib
import json
from dataclasses import asdict
from enum import Enum

from perfis_metalicos.analysis import analyze_prismatic_beam
from perfis_metalicos.domain import (
    AppliedMoment,
    BeamModel,
    ConcentratedLoad,
    Force,
    Length,
    LineLoad,
    Moment,
    SecondMomentOfArea,
    Stress,
    SupportCondition,
    UniformLineLoad,
)


def run() -> str:
    result = analyze_prismatic_beam(
        BeamModel(Length(600.0), SupportCondition.PROPPED_CANTILEVER),
        (
            UniformLineLoad(Length(0.0), Length(600.0), LineLoad(0.08)),
            ConcentratedLoad(Length(225.0), Force(12.0)),
            AppliedMoment(Length(450.0), Moment(350.0)),
        ),
        Stress(20_000.0),
        SecondMomentOfArea(12_500.0),
    )
    payload = json.dumps(
        asdict(result),
        sort_keys=True,
        separators=(",", ":"),
        default=lambda value: value.value if isinstance(value, Enum) else str(value),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


if __name__ == "__main__":
    first = run()
    second = run()
    if first != second:
        raise SystemExit("Resultado não determinístico.")
    print(f"deterministic_sha256={first}")
