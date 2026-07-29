"""Entrada canônica e registro reproduzível da análise estrutural."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from perfis_metalicos.analysis import analyze_prismatic_beam
from perfis_metalicos.domain import (
    AppliedMoment,
    BeamModel,
    ConcentratedLoad,
    Force,
    Length,
    LinearlyVaryingLoad,
    LineLoad,
    Moment,
    SecondMomentOfArea,
    Stress,
    SupportCondition,
    UniformLineLoad,
)


@dataclass(frozen=True, slots=True)
class ReproducibleAnalysisRecord:
    schema_version: str
    engine_version: str
    commit: str
    input_sha256: str
    catalog_sha256: str
    normative_manifest_sha256: str
    input_data: dict[str, Any]
    analysis_result: dict[str, Any]
    declared_scope: tuple[str, ...]
    pending_items: tuple[str, ...]
    classification: str = "NÃO VALIDADO"

    def canonical_json(self) -> str:
        return canonical_json(asdict(self))


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _load_from_payload(data: dict[str, Any]):
    load_type = data.get("type")
    if load_type == "uniform":
        return UniformLineLoad(
            Length(float(data["start_cm"])),
            Length(float(data["end_cm"])),
            LineLoad(float(data["intensity_kN_per_cm"])),
        )
    if load_type == "linear":
        return LinearlyVaryingLoad(
            Length(float(data["start_cm"])),
            Length(float(data["end_cm"])),
            LineLoad(float(data["start_intensity_kN_per_cm"])),
            LineLoad(float(data["end_intensity_kN_per_cm"])),
        )
    if load_type == "point":
        return ConcentratedLoad(
            Length(float(data["position_cm"])),
            Force(float(data["force_kN"])),
        )
    if load_type == "moment":
        return AppliedMoment(
            Length(float(data["position_cm"])),
            Moment(float(data["moment_kN_cm"])),
        )
    raise ValueError(f"Tipo de carregamento não reconhecido: {load_type!r}.")


def _extremum_payload(extremum) -> dict[str, float]:
    return {
        "value": float(extremum.value),
        "position_cm": extremum.position.cm,
    }


def build_reproducible_analysis_record(
    input_data: dict[str, Any],
    *,
    engine_version: str,
    commit: str,
    catalog_path: Path,
    normative_manifest_path: Path,
) -> ReproducibleAnalysisRecord:
    if input_data.get("schema_version") != "1.0":
        raise ValueError("Versão do JSON de entrada não suportada.")
    model_data = input_data["beam"]
    material_data = input_data["material"]
    model = BeamModel(
        Length(float(model_data["length_cm"])),
        SupportCondition[str(model_data["support"])],
    )
    loads = tuple(_load_from_payload(dict(item)) for item in input_data["loads"])
    response = analyze_prismatic_beam(
        model,
        loads,
        Stress(float(material_data["elastic_modulus_kN_per_cm2"])),
        SecondMomentOfArea(float(input_data["section"]["ix_cm4"])),
        relative_tolerance=float(input_data.get("relative_tolerance", 1e-7)),
        max_refinements=int(input_data.get("max_refinements", 8)),
    )
    canonical_input = canonical_json(input_data)
    result = {
        "reaction_left_kN": response.reaction_left.kN,
        "reaction_right_kN": response.reaction_right.kN,
        "moment_left_kN_cm": response.moment_left.kN_cm,
        "moment_right_kN_cm": response.moment_right.kN_cm,
        "maximum_moment": _extremum_payload(response.maximum_moment),
        "minimum_moment": _extremum_payload(response.minimum_moment),
        "maximum_shear": _extremum_payload(response.maximum_shear),
        "minimum_shear": _extremum_payload(response.minimum_shear),
        "maximum_deflection": _extremum_payload(response.maximum_deflection),
        "minimum_deflection": _extremum_payload(response.minimum_deflection),
        "element_count": response.element_count,
        "refinement_iterations": response.refinement_iterations,
        "estimated_relative_error": response.estimated_relative_error,
        "requested_relative_tolerance": response.requested_relative_tolerance,
        "converged": response.converged,
        "sign_convention": {
            "load_and_deflection": "positive_down",
            "reaction": "positive_up",
            "moment": "positive_sagging",
        },
    }
    pending = (
        "NORMATIVE_REVIEW_REQUIRED: regras de combinações de produção",
        "INVALID_CATALOG_DATA",
        "NOT_CHECKED: resistências e detalhamento fora deste registro de análise",
        "INDEPENDENT_EVIDENCE_REQUIRED",
    )
    return ReproducibleAnalysisRecord(
        schema_version="1.0",
        engine_version=engine_version,
        commit=commit,
        input_sha256=sha256_text(canonical_input),
        catalog_sha256=sha256_path(catalog_path),
        normative_manifest_sha256=sha256_path(normative_manifest_path),
        input_data=json.loads(canonical_input),
        analysis_result=result,
        declared_scope=(
            "Viga prismática de um vão",
            "Análise elástica linear de primeira ordem",
            "Esforços e deslocamentos para as ações explicitamente informadas",
        ),
        pending_items=pending,
    )

