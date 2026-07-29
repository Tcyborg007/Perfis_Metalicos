"""Segmentos de estabilidade lateral e associação local demanda-Cb."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Callable, Iterable

from perfis_metalicos.analysis.beam_fem import BeamAnalysisResult
from perfis_metalicos.domain.models import SupportCondition
from perfis_metalicos.domain.status import VerificationStatus
from perfis_metalicos.domain.units import Length, Moment


class Flange(Enum):
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    REVERSING = "REVERSING"


class LoadApplicationHeight(Enum):
    ABOVE_MID_DEPTH = "ABOVE_MID_DEPTH"
    AT_MID_DEPTH = "AT_MID_DEPTH"
    BELOW_MID_DEPTH = "BELOW_MID_DEPTH"


@dataclass(frozen=True, slots=True)
class RestraintPoint:
    position: Length
    top_flange_lateral: bool
    bottom_flange_lateral: bool
    torsional: bool
    warping: bool
    restraint_id: str

    def __post_init__(self) -> None:
        if not self.restraint_id.strip():
            raise ValueError("A contenção deve possuir identificação.")


@dataclass(frozen=True, slots=True)
class ContinuousFlangeRestraint:
    start: Length
    end: Length
    flange: Flange
    restraint_id: str

    def __post_init__(self) -> None:
        if self.end.cm <= self.start.cm:
            raise ValueError("Intervalo de contenção contínua inválido.")
        if self.flange is Flange.REVERSING:
            raise ValueError("A contenção contínua deve identificar uma mesa física.")


@dataclass(frozen=True, slots=True)
class UnbracedSegment:
    segment_id: str
    start: Length
    end: Length
    start_restraint: RestraintPoint
    end_restraint: RestraintPoint
    top_continuous: bool
    bottom_continuous: bool
    load_application_height: LoadApplicationHeight

    @property
    def length(self) -> Length:
        return Length(self.end.cm - self.start.cm)


@dataclass(frozen=True, slots=True)
class SegmentMomentData:
    segment: UnbracedSegment
    mmax: Moment
    mmax_position: Length
    ma: Moment
    mb: Moment
    mc: Moment
    cb: float | None
    compressed_flange: Flange
    status: VerificationStatus
    justification: str
    reference_item: str
    restraint_assumptions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SegmentFltCheck:
    moment_data: SegmentMomentData
    resistance: Moment | None
    utilization: float | None
    status: VerificationStatus
    justification: str


def build_unbraced_segments(
    beam_length: Length,
    restraint_points: Iterable[RestraintPoint],
    continuous_restraints: Iterable[ContinuousFlangeRestraint] = (),
    *,
    load_application_height: LoadApplicationHeight = LoadApplicationHeight.AT_MID_DEPTH,
) -> tuple[UnbracedSegment, ...]:
    points = tuple(sorted(restraint_points, key=lambda item: item.position.cm))
    if len(points) < 2:
        raise ValueError("São necessárias contenções em pelo menos duas posições.")
    if not math.isclose(points[0].position.cm, 0.0, abs_tol=1e-9):
        raise ValueError("A primeira contenção deve estar em x=0.")
    if not math.isclose(points[-1].position.cm, beam_length.cm, abs_tol=1e-9):
        raise ValueError("A última contenção deve estar em x=L.")
    if len({point.position.cm for point in points}) != len(points):
        raise ValueError("Posições de contenção duplicadas.")
    intervals = tuple(continuous_restraints)
    segments: list[UnbracedSegment] = []
    for index, (start, end) in enumerate(zip(points, points[1:]), start=1):
        top = any(
            item.flange is Flange.TOP
            and item.start.cm <= start.position.cm + 1e-9
            and item.end.cm >= end.position.cm - 1e-9
            for item in intervals
        )
        bottom = any(
            item.flange is Flange.BOTTOM
            and item.start.cm <= start.position.cm + 1e-9
            and item.end.cm >= end.position.cm - 1e-9
            for item in intervals
        )
        segments.append(
            UnbracedSegment(
                segment_id=f"SEG-{index:03d}",
                start=start.position,
                end=end.position,
                start_restraint=start,
                end_restraint=end,
                top_continuous=top,
                bottom_continuous=bottom,
                load_application_height=load_application_height,
            )
        )
    return tuple(segments)


def _segment_candidates(
    response: BeamAnalysisResult,
    segment: UnbracedSegment,
) -> tuple[float, ...]:
    start, end = segment.start.cm, segment.end.cm
    points = {start, end}
    for load in response.loads:
        if hasattr(load, "start"):
            if start <= load.start.cm <= end:
                points.add(load.start.cm)
            if start <= load.end.cm <= end:
                points.add(load.end.cm)
        elif start <= load.position.cm <= end:
            points.add(load.position.cm)
    ordered = sorted(points)
    for left, right in zip(ordered, ordered[1:]):
        v_left = response.shear_at(math.nextafter(left, right))
        v_right = response.shear_at(math.nextafter(right, left))
        if v_left * v_right < 0:
            low, high = left, right
            for _ in range(80):
                middle = (low + high) / 2.0
                value = response.shear_at(middle)
                if v_left * value <= 0:
                    high = middle
                else:
                    low = middle
                    v_left = value
            points.add((low + high) / 2.0)
    return tuple(sorted(points))


def _compressed_flange(response: BeamAnalysisResult, candidates: tuple[float, ...]) -> Flange:
    tolerance = max(
        max(abs(response.moment_at(x)) for x in candidates) * 1e-10,
        1e-9,
    )
    signs = {
        1 if response.moment_at(x) > 0 else -1
        for x in candidates
        if abs(response.moment_at(x)) > tolerance
    }
    if signs == {1}:
        return Flange.TOP
    if signs == {-1}:
        return Flange.BOTTOM
    return Flange.REVERSING


def _restraint_deficiencies(
    segment: UnbracedSegment,
    compressed_flange: Flange,
) -> tuple[str, ...]:
    """Retorna componentes mínimos ausentes no modelo computacional do trecho.

    A função não dimensiona a contenção. Os booleanos representam contenções cuja
    eficácia já deve ter sido demonstrada fora deste cálculo. A resistência e a
    rigidez dos dispositivos continuam sendo evidência externa obrigatória.
    """

    deficiencies: list[str] = []
    endpoints = (
        ("inicial", segment.start_restraint),
        ("final", segment.end_restraint),
    )
    required_flanges = (
        (Flange.TOP, Flange.BOTTOM)
        if compressed_flange is Flange.REVERSING
        else (compressed_flange,)
    )
    for endpoint_name, restraint in endpoints:
        for flange in required_flanges:
            is_laterally_restrained = (
                restraint.top_flange_lateral
                if flange is Flange.TOP
                else restraint.bottom_flange_lateral
            )
            if not is_laterally_restrained:
                deficiencies.append(
                    f"contenção lateral da mesa {flange.value} na extremidade "
                    f"{endpoint_name}"
                )
        if not restraint.torsional:
            deficiencies.append(f"contenção torcional na extremidade {endpoint_name}")
    return tuple(deficiencies)


def segment_moment_data(
    response: BeamAnalysisResult,
    segment: UnbracedSegment,
) -> SegmentMomentData:
    start, length = segment.start.cm, segment.length.cm
    candidates = _segment_candidates(response, segment)
    mmax_position = max(candidates, key=lambda x: abs(response.moment_at(x)))
    mmax = abs(response.moment_at(mmax_position))
    ma = abs(response.moment_at(start + length / 4.0))
    mb = abs(response.moment_at(start + length / 2.0))
    mc = abs(response.moment_at(start + 3.0 * length / 4.0))
    compressed = _compressed_flange(response, candidates)

    common = {
        "segment": segment,
        "mmax": Moment(mmax),
        "mmax_position": Length(mmax_position),
        "ma": Moment(ma),
        "mb": Moment(mb),
        "mc": Moment(mc),
        "compressed_flange": compressed,
    }
    if segment.load_application_height is LoadApplicationHeight.ABOVE_MID_DEPTH:
        return SegmentMomentData(
            **common,
            cb=None,
            status=VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED,
            justification=(
                "Força desestabilizante acima da semialtura exige análise de estabilidade "
                "ou procedimento aceito."
            ),
            reference_item="ABNT NBR 8800:2024, 5.4.2.3",
        )
    if segment.top_continuous != segment.bottom_continuous:
        return SegmentMomentData(
            **common,
            cb=None,
            status=VerificationStatus.NOT_CHECKED,
            justification=(
                "Uma única mesa possui contenção lateral contínua; aplicar o procedimento "
                "específico somente após revisão completa de 5.4.2.4."
            ),
            reference_item="ABNT NBR 8800:2024, 5.4.2.4",
        )
    if segment.top_continuous and segment.bottom_continuous:
        return SegmentMomentData(
            **common,
            cb=None,
            status=VerificationStatus.NOT_CHECKED,
            justification=(
                "A eficácia da contenção contínua das duas mesas ainda não foi verificada."
            ),
            reference_item="ABNT NBR 8800:2024, 4.12 e 5.4.2",
        )
    if response.model.support is SupportCondition.CANTILEVER:
        return SegmentMomentData(
            **common,
            cb=None,
            status=VerificationStatus.NOT_CHECKED,
            justification=(
                "O balanço exige classificação explícita das restrições laterais, "
                "torcionais e de empenamento antes da seleção de Cb."
            ),
            reference_item="ABNT NBR 8800:2024, 5.4.2.3-b",
        )
    deficiencies = _restraint_deficiencies(segment, compressed)
    if deficiencies:
        return SegmentMomentData(
            **common,
            cb=None,
            status=VerificationStatus.EXTERNAL_EVIDENCE_REQUIRED,
            justification=(
                "O trecho não possui todas as contenções eficazes requeridas pelo "
                "modelo computacional: " + "; ".join(deficiencies) + "."
            ),
            reference_item="ABNT NBR 8800:2024, 4.12 e 5.4.2.3",
            restraint_assumptions=(
                "A resistência e a rigidez das contenções não são dimensionadas por "
                "este módulo.",
            ),
        )
    denominator = 2.5 * mmax + 3.0 * ma + 4.0 * mb + 3.0 * mc
    cb_calculated = 1.0 if denominator <= 0 else 12.5 * mmax / denominator
    cb = min(cb_calculated, 3.0)
    return SegmentMomentData(
        **common,
        cb=cb,
        status=VerificationStatus.PASS,
        justification=(
            "Cb calculado com momentos do próprio comprimento destravado e limitado "
            "a 3,0."
        ),
        reference_item="ABNT NBR 8800:2024, 5.4.2.3-a",
        restraint_assumptions=(
            "Os indicadores de contenção lateral e torcional representam contenções "
            "eficazes previamente verificadas.",
            "A restrição ao empenamento foi registrada, mas não foi tomada como "
            "condição automática do caso geral.",
        ),
    )


ResistanceProvider = Callable[[UnbracedSegment, float], Moment]


def evaluate_flt_segments(
    response: BeamAnalysisResult,
    segments: Iterable[UnbracedSegment],
    resistance_provider: ResistanceProvider,
) -> tuple[SegmentFltCheck, ...]:
    checks: list[SegmentFltCheck] = []
    for segment in segments:
        data = segment_moment_data(response, segment)
        if data.status is not VerificationStatus.PASS or data.cb is None:
            checks.append(
                SegmentFltCheck(
                    moment_data=data,
                    resistance=None,
                    utilization=None,
                    status=data.status,
                    justification=data.justification,
                )
            )
            continue
        resistance = resistance_provider(segment, data.cb)
        if resistance.kN_cm <= 0:
            checks.append(
                SegmentFltCheck(
                    moment_data=data,
                    resistance=resistance,
                    utilization=None,
                    status=VerificationStatus.INVALID_INPUT,
                    justification="A resistência do segmento deve ser positiva.",
                )
            )
            continue
        utilization = data.mmax.kN_cm / resistance.kN_cm
        checks.append(
            SegmentFltCheck(
                moment_data=data,
                resistance=resistance,
                utilization=utilization,
                status=(
                    VerificationStatus.PASS
                    if utilization <= 1.0
                    else VerificationStatus.FAIL
                ),
                justification=(
                    "Demanda, Cb e resistência pertencem ao mesmo segmento destravado."
                ),
            )
        )
    return tuple(checks)


def governing_flt_segment(
    checks: Iterable[SegmentFltCheck],
) -> SegmentFltCheck | None:
    comparable = tuple(item for item in checks if item.utilization is not None)
    return max(comparable, key=lambda item: item.utilization) if comparable else None
