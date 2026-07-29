"""Análise de viga prismática Euler-Bernoulli por elementos finitos.

Convenções:
- deslocamento transversal e cargas positivas para baixo;
- reação vertical positiva para cima;
- momento interno sagente positivo;
- momento aplicado positivo no sentido do grau de liberdade de rotação.

As posições críticas de deslocamento não são procuradas em uma malha de
amostragem. A rotação quadrática de cada elemento cúbico é resolvida para zero.
O refinamento da malha controla o erro estimado da resposta.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from perfis_metalicos.domain.actions import (
    AppliedMoment,
    ConcentratedLoad,
    LinearlyVaryingLoad,
    Load,
    UniformLineLoad,
)
from perfis_metalicos.domain.models import BeamModel, SupportCondition
from perfis_metalicos.domain.units import (
    Force,
    Length,
    Moment,
    SecondMomentOfArea,
    Stress,
)


@dataclass(frozen=True, slots=True)
class BeamExtremum:
    value: float
    position: Length


@dataclass(frozen=True, slots=True)
class BeamElementResponse:
    start: float
    end: float
    displacement_coefficients: tuple[float, float, float, float]

    @property
    def length(self) -> float:
        return self.end - self.start

    def displacement_at(self, x: float) -> float:
        r = (x - self.start) / self.length
        a0, a1, a2, a3 = self.displacement_coefficients
        return a0 + a1 * r + a2 * r**2 + a3 * r**3

    def rotation_at(self, x: float) -> float:
        r = (x - self.start) / self.length
        _, a1, a2, a3 = self.displacement_coefficients
        return (a1 + 2.0 * a2 * r + 3.0 * a3 * r**2) / self.length

    def curvature_at(self, x: float) -> float:
        r = (x - self.start) / self.length
        _, _, a2, a3 = self.displacement_coefficients
        return (2.0 * a2 + 6.0 * a3 * r) / self.length**2

    def rotation_roots(self) -> tuple[float, ...]:
        _, a1, a2, a3 = self.displacement_coefficients
        roots = np.roots((3.0 * a3, 2.0 * a2, a1))
        positions: list[float] = []
        for root in roots:
            if abs(root.imag) <= 1e-10 and 0.0 < root.real < 1.0:
                positions.append(self.start + float(root.real) * self.length)
        return tuple(sorted(set(positions)))


@dataclass(frozen=True, slots=True)
class BeamAnalysisResult:
    model: BeamModel
    reaction_left: Force
    reaction_right: Force
    moment_left: Moment
    moment_right: Moment
    maximum_moment: BeamExtremum
    minimum_moment: BeamExtremum
    maximum_shear: BeamExtremum
    minimum_shear: BeamExtremum
    maximum_deflection: BeamExtremum
    minimum_deflection: BeamExtremum
    elements: tuple[BeamElementResponse, ...]
    loads: tuple[Load, ...]
    element_count: int
    refinement_iterations: int
    estimated_relative_error: float
    requested_relative_tolerance: float
    converged: bool

    def _element_at(self, x: float) -> BeamElementResponse:
        coordinate = min(max(float(x), 0.0), self.model.length.cm)
        for element in self.elements:
            if element.start - 1e-12 <= coordinate <= element.end + 1e-12:
                return element
        raise ValueError("Posição fora da viga.")

    def displacement_at(self, x: float) -> float:
        return self._element_at(x).displacement_at(float(x))

    def rotation_at(self, x: float) -> float:
        return self._element_at(x).rotation_at(float(x))

    def shear_at(self, x: float, after_point: bool = True) -> float:
        coordinate = min(max(float(x), 0.0), self.model.length.cm)
        value = self.reaction_left.kN
        for load in self.loads:
            if isinstance(load, UniformLineLoad):
                covered = min(max(coordinate - load.start.cm, 0.0), load.end.cm - load.start.cm)
                value -= load.intensity.kN_per_cm * covered
            elif isinstance(load, LinearlyVaryingLoad):
                covered = min(max(coordinate - load.start.cm, 0.0), load.end.cm - load.start.cm)
                if covered > 0:
                    span = load.end.cm - load.start.cm
                    slope = (
                        load.end_intensity.kN_per_cm
                        - load.start_intensity.kN_per_cm
                    ) / span
                    value -= load.start_intensity.kN_per_cm * covered
                    value -= 0.5 * slope * covered**2
            elif isinstance(load, ConcentratedLoad):
                if coordinate > load.position.cm or (
                    after_point and math.isclose(coordinate, load.position.cm)
                ):
                    value -= load.force.kN
        return value

    def moment_at(self, x: float, after_moment: bool = True) -> float:
        coordinate = min(max(float(x), 0.0), self.model.length.cm)
        value = self.moment_left.kN_cm + self.reaction_left.kN * coordinate
        for load in self.loads:
            if isinstance(load, UniformLineLoad):
                covered = min(max(coordinate - load.start.cm, 0.0), load.end.cm - load.start.cm)
                if covered > 0:
                    resultant = load.intensity.kN_per_cm * covered
                    centroid = load.start.cm + covered / 2.0
                    value -= resultant * (coordinate - centroid)
            elif isinstance(load, LinearlyVaryingLoad):
                covered = min(max(coordinate - load.start.cm, 0.0), load.end.cm - load.start.cm)
                if covered > 0:
                    span = load.end.cm - load.start.cm
                    slope = (
                        load.end_intensity.kN_per_cm
                        - load.start_intensity.kN_per_cm
                    ) / span
                    q0 = load.start_intensity.kN_per_cm
                    resultant = q0 * covered + 0.5 * slope * covered**2
                    first_moment_local = (
                        0.5 * q0 * covered**2
                        + slope * covered**3 / 3.0
                    )
                    value -= resultant * (coordinate - load.start.cm)
                    value += first_moment_local
            elif isinstance(load, ConcentratedLoad):
                if coordinate >= load.position.cm:
                    value -= load.force.kN * (coordinate - load.position.cm)
            elif isinstance(load, AppliedMoment):
                if coordinate > load.position.cm or (
                    after_moment and math.isclose(coordinate, load.position.cm)
                ):
                    value -= load.moment.kN_cm
        return value


@dataclass(frozen=True, slots=True)
class _Solution:
    nodes: np.ndarray
    displacements: np.ndarray
    reactions: np.ndarray
    elements: tuple[BeamElementResponse, ...]
    reaction_left: float
    reaction_right: float
    moment_left: float
    moment_right: float
    max_deflection: BeamExtremum
    min_deflection: BeamExtremum


def _load_breakpoints(loads: tuple[Load, ...], length: float) -> tuple[float, ...]:
    points = {0.0, length}
    for load in loads:
        if isinstance(load, (UniformLineLoad, LinearlyVaryingLoad)):
            points.update((load.start.cm, load.end.cm))
        else:
            points.add(load.position.cm)
    return tuple(sorted(points))


def _validate_loads(loads: tuple[Load, ...], length: float) -> None:
    if not loads:
        raise ValueError("Ao menos um carregamento é obrigatório.")
    for load in loads:
        if isinstance(load, (UniformLineLoad, LinearlyVaryingLoad)):
            if load.start.cm < 0 or load.end.cm > length:
                raise ValueError("Carga distribuída fora do vão.")
        elif load.position.cm < 0 or load.position.cm > length:
            raise ValueError("Carga concentrada ou momento fora do vão.")


def _nodes_for(
    breakpoints: tuple[float, ...],
    subdivisions: int,
) -> np.ndarray:
    nodes: list[float] = [breakpoints[0]]
    for start, end in zip(breakpoints, breakpoints[1:], strict=False):
        nodes.extend(
            start + (end - start) * index / subdivisions
            for index in range(1, subdivisions + 1)
        )
    return np.array(nodes, dtype=float)


def _distributed_intensity(loads: tuple[Load, ...], x: float) -> float:
    total = 0.0
    for load in loads:
        if isinstance(load, UniformLineLoad):
            if load.start.cm - 1e-12 <= x <= load.end.cm + 1e-12:
                total += load.intensity.kN_per_cm
        elif isinstance(load, LinearlyVaryingLoad):
            if load.start.cm - 1e-12 <= x <= load.end.cm + 1e-12:
                ratio = (x - load.start.cm) / (load.end.cm - load.start.cm)
                total += (
                    load.start_intensity.kN_per_cm
                    + ratio
                    * (
                        load.end_intensity.kN_per_cm
                        - load.start_intensity.kN_per_cm
                    )
                )
    return total


def _shape_functions(r: float, length: float) -> np.ndarray:
    return np.array(
        (
            1.0 - 3.0 * r**2 + 2.0 * r**3,
            length * (r - 2.0 * r**2 + r**3),
            3.0 * r**2 - 2.0 * r**3,
            length * (-r**2 + r**3),
        )
    )


def _element_stiffness(flexural_rigidity: float, length: float) -> np.ndarray:
    scale = flexural_rigidity / length**3
    return scale * np.array(
        (
            (12.0, 6.0 * length, -12.0, 6.0 * length),
            (6.0 * length, 4.0 * length**2, -6.0 * length, 2.0 * length**2),
            (-12.0, -6.0 * length, 12.0, -6.0 * length),
            (6.0 * length, 2.0 * length**2, -6.0 * length, 4.0 * length**2),
        )
    )


def _constraints(support: SupportCondition, node_count: int) -> tuple[int, ...]:
    last_v = 2 * (node_count - 1)
    last_theta = last_v + 1
    if support is SupportCondition.SIMPLY_SUPPORTED:
        return (0, last_v)
    if support is SupportCondition.CANTILEVER:
        return (0, 1)
    if support is SupportCondition.FIXED_FIXED:
        return (0, 1, last_v, last_theta)
    if support is SupportCondition.PROPPED_CANTILEVER:
        return (0, 1, last_v)
    raise ValueError("Vínculo não suportado.")


def _element_coefficients(dofs: np.ndarray, length: float) -> tuple[float, float, float, float]:
    v1, theta1, v2, theta2 = map(float, dofs)
    return (
        v1,
        length * theta1,
        -3.0 * v1 - 2.0 * length * theta1 + 3.0 * v2 - length * theta2,
        2.0 * v1 + length * theta1 - 2.0 * v2 + length * theta2,
    )


def _solve_once(
    model: BeamModel,
    loads: tuple[Load, ...],
    elastic_modulus: Stress,
    inertia: SecondMomentOfArea,
    breakpoints: tuple[float, ...],
    subdivisions: int,
) -> _Solution:
    nodes = _nodes_for(breakpoints, subdivisions)
    dof_count = 2 * len(nodes)
    stiffness = np.zeros((dof_count, dof_count))
    forces = np.zeros(dof_count)
    flexural_rigidity = (
        elastic_modulus.kN_per_cm2 * inertia.cm4
    )
    gauss_x, gauss_w = np.polynomial.legendre.leggauss(3)

    for index, (start, end) in enumerate(zip(nodes, nodes[1:], strict=False)):
        length = end - start
        indices = np.array((2 * index, 2 * index + 1, 2 * index + 2, 2 * index + 3))
        stiffness[np.ix_(indices, indices)] += _element_stiffness(
            flexural_rigidity, length
        )
        equivalent = np.zeros(4)
        for xi, weight in zip(gauss_x, gauss_w, strict=True):
            r = (xi + 1.0) / 2.0
            coordinate = start + r * length
            equivalent += (
                _shape_functions(r, length)
                * _distributed_intensity(loads, coordinate)
                * weight
                * length
                / 2.0
            )
        forces[indices] += equivalent

    for load in loads:
        if isinstance(load, (ConcentratedLoad, AppliedMoment)):
            node_index = int(np.argmin(np.abs(nodes - load.position.cm)))
            if not math.isclose(nodes[node_index], load.position.cm, abs_tol=1e-9):
                raise RuntimeError("A malha não contém a posição da carga concentrada.")
            dof = 2 * node_index
            if isinstance(load, ConcentratedLoad):
                forces[dof] += load.force.kN
            else:
                forces[dof + 1] += load.moment.kN_cm

    constrained = set(_constraints(model.support, len(nodes)))
    free = np.array(
        [index for index in range(dof_count) if index not in constrained],
        dtype=int,
    )
    displacements = np.zeros(dof_count)
    if free.size:
        displacements[free] = np.linalg.solve(
            stiffness[np.ix_(free, free)],
            forces[free],
        )
    reactions = stiffness @ displacements - forces

    elements: list[BeamElementResponse] = []
    critical_positions = {0.0, model.length.cm}
    for index, (start, end) in enumerate(zip(nodes, nodes[1:], strict=False)):
        indices = np.array((2 * index, 2 * index + 1, 2 * index + 2, 2 * index + 3))
        element = BeamElementResponse(
            start=float(start),
            end=float(end),
            displacement_coefficients=_element_coefficients(
                displacements[indices], end - start
            ),
        )
        elements.append(element)
        critical_positions.update((float(start), float(end)))
        critical_positions.update(element.rotation_roots())

    def displacement_at(position: float) -> float:
        for element in elements:
            if element.start - 1e-12 <= position <= element.end + 1e-12:
                return element.displacement_at(position)
        raise RuntimeError("Posição crítica fora da malha.")

    max_position = max(critical_positions, key=displacement_at)
    min_position = min(critical_positions, key=displacement_at)
    if model.support is SupportCondition.SIMPLY_SUPPORTED:
        moment_left = 0.0
        moment_right = 0.0
    elif model.support is SupportCondition.CANTILEVER:
        moment_left = float(reactions[1])
        moment_right = 0.0
    elif model.support is SupportCondition.PROPPED_CANTILEVER:
        moment_left = float(reactions[1])
        moment_right = 0.0
    else:
        moment_left = float(reactions[1])
        moment_right = -float(reactions[-1])
    return _Solution(
        nodes=nodes,
        displacements=displacements,
        reactions=reactions,
        elements=tuple(elements),
        reaction_left=-float(reactions[0]),
        reaction_right=-float(reactions[-2]),
        moment_left=moment_left,
        moment_right=moment_right,
        max_deflection=BeamExtremum(displacement_at(max_position), Length(max_position)),
        min_deflection=BeamExtremum(displacement_at(min_position), Length(min_position)),
    )


def _response_candidates(
    model: BeamModel,
    loads: tuple[Load, ...],
    provisional: BeamAnalysisResult,
) -> tuple[float, ...]:
    boundaries = set(_load_breakpoints(loads, model.length.cm))
    candidates = set(boundaries)
    ordered = sorted(boundaries)
    for start, end in zip(ordered, ordered[1:], strict=False):
        left = math.nextafter(start, end)
        right = math.nextafter(end, start)
        v_left = provisional.shear_at(left)
        v_right = provisional.shear_at(right)
        if math.isclose(v_left, 0.0, abs_tol=1e-10):
            candidates.add(start)
        if v_left * v_right < 0:
            low, high = start, end
            for _ in range(80):
                middle = (low + high) / 2.0
                value = provisional.shear_at(middle)
                if v_left * value <= 0:
                    high = middle
                    v_right = value
                else:
                    low = middle
                    v_left = value
            candidates.add((low + high) / 2.0)
    return tuple(sorted(candidates))


def analyze_prismatic_beam(
    model: BeamModel,
    loads: Iterable[Load],
    elastic_modulus: Stress,
    inertia: SecondMomentOfArea,
    *,
    relative_tolerance: float = 1e-7,
    max_refinements: int = 8,
) -> BeamAnalysisResult:
    model.length.require_positive("Vão")
    elastic_modulus.require_positive("E")
    inertia.require_positive("I")
    if relative_tolerance <= 0 or not math.isfinite(relative_tolerance):
        raise ValueError("A tolerância relativa deve ser positiva e finita.")
    if max_refinements < 2:
        raise ValueError("Use ao menos dois refinamentos.")

    values = tuple(loads)
    _validate_loads(values, model.length.cm)
    breakpoints = _load_breakpoints(values, model.length.cm)
    previous: _Solution | None = None
    error = math.inf
    converged = False
    current: _Solution | None = None

    for iteration in range(1, max_refinements + 1):
        subdivisions = 2 ** (iteration - 1)
        current = _solve_once(
            model,
            values,
            elastic_modulus,
            inertia,
            breakpoints,
            subdivisions,
        )
        if previous is not None:
            current_abs = max(
                abs(current.max_deflection.value),
                abs(current.min_deflection.value),
            )
            previous_abs = max(
                abs(previous.max_deflection.value),
                abs(previous.min_deflection.value),
            )
            scale = max(current_abs, 1e-15)
            error = abs(current_abs - previous_abs) / scale
            if error <= relative_tolerance:
                converged = True
                break
        previous = current

    assert current is not None
    provisional = BeamAnalysisResult(
        model=model,
        reaction_left=Force(current.reaction_left),
        reaction_right=Force(current.reaction_right),
        moment_left=Moment(current.moment_left),
        moment_right=Moment(current.moment_right),
        maximum_moment=BeamExtremum(0.0, Length(0.0)),
        minimum_moment=BeamExtremum(0.0, Length(0.0)),
        maximum_shear=BeamExtremum(0.0, Length(0.0)),
        minimum_shear=BeamExtremum(0.0, Length(0.0)),
        maximum_deflection=current.max_deflection,
        minimum_deflection=current.min_deflection,
        elements=current.elements,
        loads=values,
        element_count=len(current.elements),
        refinement_iterations=iteration,
        estimated_relative_error=error,
        requested_relative_tolerance=relative_tolerance,
        converged=converged,
    )
    candidates = _response_candidates(model, values, provisional)
    moment_values: list[tuple[float, float]] = []
    shear_values: list[tuple[float, float]] = []
    for position in candidates:
        moment_values.extend(
            (
                (provisional.moment_at(position, after_moment=False), position),
                (provisional.moment_at(position, after_moment=True), position),
            )
        )
        shear_values.extend(
            (
                (provisional.shear_at(position, after_point=False), position),
                (provisional.shear_at(position, after_point=True), position),
            )
        )
    max_moment, max_moment_position = max(moment_values)
    min_moment, min_moment_position = min(moment_values)
    max_shear, max_shear_position = max(shear_values)
    min_shear, min_shear_position = min(shear_values)
    return BeamAnalysisResult(
        model=model,
        reaction_left=provisional.reaction_left,
        reaction_right=provisional.reaction_right,
        moment_left=provisional.moment_left,
        moment_right=provisional.moment_right,
        maximum_moment=BeamExtremum(max_moment, Length(max_moment_position)),
        minimum_moment=BeamExtremum(min_moment, Length(min_moment_position)),
        maximum_shear=BeamExtremum(max_shear, Length(max_shear_position)),
        minimum_shear=BeamExtremum(min_shear, Length(min_shear_position)),
        maximum_deflection=provisional.maximum_deflection,
        minimum_deflection=provisional.minimum_deflection,
        elements=provisional.elements,
        loads=values,
        element_count=provisional.element_count,
        refinement_iterations=provisional.refinement_iterations,
        estimated_relative_error=provisional.estimated_relative_error,
        requested_relative_tolerance=provisional.requested_relative_tolerance,
        converged=provisional.converged,
    )
