"""Núcleo de cálculo para vigas I/H conforme ABNT NBR 8800:2024 + Errata 1:2025.

Unidades internas: kN e cm. O módulo de elasticidade e as resistências são
informados em kN/cm². Este módulo é deliberadamente independente do Streamlit
para permitir ensaios unitários e revisão das equações.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


NORMA = "ABNT NBR 8800:2024"
ERRATA = "ABNT NBR 8800:2024/Er1:2025 — Errata 1 (25/02/2025)"
GAMMA_A1 = 1.10
GAMMA_A2 = 1.35

SUPPORT_ALIASES = {
    "Bi-apoiada": "simply_supported",
    "Engastada e Livre (Balanço)": "cantilever",
    "Bi-engastada": "fixed_fixed",
    "Engastada e Apoiada": "propped_cantilever",
    "simply_supported": "simply_supported",
    "cantilever": "cantilever",
    "fixed_fixed": "fixed_fixed",
    "propped_cantilever": "propped_cantilever",
}


@dataclass(frozen=True)
class BeamResponse:
    support: str
    length: float
    q: float
    point_load: float
    point_position: float
    reaction_left: float
    reaction_right: float
    moment_left: float
    moment_right: float
    max_moment: float
    max_moment_position: float
    max_shear: float
    max_deflection: float
    max_deflection_position: float
    x: tuple[float, ...]
    moments: tuple[float, ...]
    shears: tuple[float, ...]
    deflections: tuple[float, ...]
    rotation_integration_constant: float

    def moment_at(self, x_value: float) -> float:
        x_value = min(max(float(x_value), 0.0), self.length)
        macaulay = max(x_value - self.point_position, 0.0)
        return (
            self.moment_left
            + self.reaction_left * x_value
            - self.q * x_value**2 / 2.0
            - self.point_load * macaulay
        )


def _validate_beam_inputs(length: float, q: float, point_load: float, point_position: float) -> None:
    if length <= 0:
        raise ValueError("O comprimento da viga deve ser positivo.")
    if q < 0 or point_load < 0:
        raise ValueError("Este modelo admite cargas gravitacionais não negativas.")
    if not 0 <= point_position <= length:
        raise ValueError("A posição da carga pontual deve estar dentro do vão.")


def _beam_end_actions(
    support: str, length: float, q: float, point_load: float, point_position: float
) -> tuple[float, float, float, float]:
    """Retorna RA, RB, M(0) e M(L), com momento sagente positivo."""
    L, P, a = length, point_load, point_position
    b = L - a

    if support == "simply_supported":
        rb = q * L / 2.0 + (P * a / L if L else 0.0)
        ra = q * L + P - rb
        m0 = 0.0
    elif support == "cantilever":
        ra, rb = q * L + P, 0.0
        m0 = -(q * L**2 / 2.0 + P * a)
    elif support == "fixed_fixed":
        ra = q * L / 2.0 + (P * b**2 * (3.0 * a + b) / L**3 if P else 0.0)
        rb = q * L + P - ra
        m0 = -q * L**2 / 12.0 - (P * a * b**2 / L**2 if P else 0.0)
    elif support == "propped_cantilever":
        rb = 3.0 * q * L / 8.0
        if P:
            rb += P * a**2 * (3.0 * L - a) / (2.0 * L**3)
        ra = q * L + P - rb
        m0 = rb * L - q * L**2 / 2.0 - P * a
    else:
        raise ValueError(f"Vinculação não suportada: {support}")

    mL = m0 + ra * L - q * L**2 / 2.0 - P * max(L - a, 0.0)
    return ra, rb, m0, mL


def analyze_beam(
    support: str,
    length: float,
    q: float = 0.0,
    point_load: float = 0.0,
    point_position: float | None = None,
    E: float | None = None,
    I: float | None = None,
    samples: int = 2001,
) -> BeamResponse:
    """Análise elástica de primeira ordem para q uniforme e uma carga pontual.

    As expressões de esforços e deslocamentos são obtidas por funções de
    singularidade. Assim, q e P são combinados na mesma seção, sem somar máximos
    que ocorram em posições distintas.
    """
    normalized = SUPPORT_ALIASES.get(support)
    if normalized is None:
        raise ValueError(f"Vinculação não suportada: {support}")
    a = length / 2.0 if point_position is None else float(point_position)
    _validate_beam_inputs(length, q, point_load, a)
    if samples < 101:
        raise ValueError("Use ao menos 101 pontos para localizar a flecha máxima.")

    ra, rb, m0, mL = _beam_end_actions(normalized, length, q, point_load, a)
    L, P = length, point_load

    def moment(xv: float) -> float:
        return m0 + ra * xv - q * xv**2 / 2.0 - P * max(xv - a, 0.0)

    def shear(xv: float, after_point: bool = True) -> float:
        p_term = P if (xv > a or (after_point and math.isclose(xv, a))) else 0.0
        return ra - q * xv - p_term

    # Constante de integração da rotação. Nos três modelos engastados ela é zero.
    c1 = 0.0
    if normalized == "simply_supported":
        end_without_c1 = (
            m0 * L**2 / 2.0
            + ra * L**3 / 6.0
            - q * L**4 / 24.0
            - P * max(L - a, 0.0) ** 3 / 6.0
        )
        c1 = -end_without_c1 / L

    use_deflection = E is not None and I is not None and E > 0 and I > 0

    def displacement(xv: float) -> float:
        if not use_deflection:
            return 0.0
        numerator = (
            c1 * xv
            + m0 * xv**2 / 2.0
            + ra * xv**3 / 6.0
            - q * xv**4 / 24.0
            - P * max(xv - a, 0.0) ** 3 / 6.0
        )
        return numerator / (E * I)

    xs = [L * i / (samples - 1) for i in range(samples)]
    if 0.0 < a < L and all(not math.isclose(xv, a, abs_tol=L / samples) for xv in xs):
        xs.append(a)
        xs.sort()
    moments = [moment(xv) for xv in xs]
    shears = [shear(xv) for xv in xs]
    deflections = [displacement(xv) for xv in xs]

    # Pontos exatos de extremo de M: extremidades, descontinuidade e V=0.
    candidates = {0.0, L, a}
    if q > 0:
        root_before = ra / q
        root_after = (ra - P) / q
        if 0.0 <= root_before <= a:
            candidates.add(root_before)
        if a <= root_after <= L:
            candidates.add(root_after)
    max_m_x = max(candidates, key=lambda xv: abs(moment(xv)))
    max_m = abs(moment(max_m_x))

    shear_candidates = [abs(ra), abs(ra - q * a), abs(ra - q * a - P), abs(-rb)]
    max_v = max(shear_candidates)
    max_d_index = max(range(len(xs)), key=lambda idx: abs(deflections[idx]))

    return BeamResponse(
        support=normalized,
        length=L,
        q=q,
        point_load=P,
        point_position=a,
        reaction_left=ra,
        reaction_right=rb,
        moment_left=m0,
        moment_right=mL,
        max_moment=max_m,
        max_moment_position=max_m_x,
        max_shear=max_v,
        max_deflection=abs(deflections[max_d_index]),
        max_deflection_position=xs[max_d_index],
        x=tuple(xs),
        moments=tuple(moments),
        shears=tuple(shears),
        deflections=tuple(deflections),
        rotation_integration_constant=c1,
    )


def calculate_cb(
    response: BeamResponse, segment_start: float = 0.0, unbraced_length: float | None = None
) -> dict:
    """Calcula Cb para seção duplamente simétrica conforme 5.4.2.3-a."""
    lb = response.length if unbraced_length is None else unbraced_length
    if lb <= 0 or segment_start < 0 or segment_start + lb > response.length + 1e-9:
        raise ValueError("O trecho destravado deve estar contido no comprimento da viga.")
    x0, x1 = segment_start, segment_start + lb
    quarter_points = [x0 + lb / 4.0, x0 + lb / 2.0, x0 + 3.0 * lb / 4.0]
    ma, mb, mc = [abs(response.moment_at(xv)) for xv in quarter_points]
    values = [abs(response.moment_at(x0)), abs(response.moment_at(x1)), ma, mb, mc]
    for xv, mv in zip(response.x, response.moments):
        if x0 <= xv <= x1:
            values.append(abs(mv))
    mmax = max(values, default=0.0)
    denominator = 2.5 * mmax + 3.0 * ma + 4.0 * mb + 3.0 * mc
    cb = 1.0 if denominator <= 0 else 12.5 * mmax / denominator
    return {
        "Cb": cb,
        "Mmax": mmax,
        "MA": ma,
        "MB": mb,
        "MC": mc,
        "xA": quarter_points[0],
        "xB": quarter_points[1],
        "xC": quarter_points[2],
        "segment_start": x0,
        "Lb": lb,
        "reference": "ABNT NBR 8800:2024, 5.4.2.3-a",
    }


def combine_elu_normal(
    q_permanent: float,
    q_variable: float,
    self_weight: float,
    point_permanent: float = 0.0,
    point_variable: float = 0.0,
    gamma_g: float = 1.50,
    gamma_q: float = 1.50,
    gamma_self_weight: float = 1.25,
) -> dict:
    """Combinação última normal para uma ação variável principal."""
    values = [q_permanent, q_variable, self_weight, point_permanent, point_variable]
    if any(value < 0 for value in values):
        raise ValueError("A rotina simplificada de gravidade não admite ações favoráveis negativas.")
    return {
        "q": gamma_g * q_permanent + gamma_self_weight * self_weight + gamma_q * q_variable,
        "P": gamma_g * point_permanent + gamma_q * point_variable,
        "q_permanent": q_permanent,
        "q_variable": q_variable,
        "self_weight": self_weight,
        "point_permanent": point_permanent,
        "point_variable": point_variable,
        "gamma_g": gamma_g,
        "gamma_q": gamma_q,
        "gamma_self_weight": gamma_self_weight,
        "reference": "ABNT NBR 8800:2024, 4.8.7.2.1 e Tabela 1",
    }


def combine_els(
    q_permanent: float,
    q_variable: float,
    self_weight: float,
    point_permanent: float = 0.0,
    point_variable: float = 0.0,
    combination: str = "rare",
    psi1: float = 0.6,
    psi2: float = 0.4,
) -> dict:
    values = [q_permanent, q_variable, self_weight, point_permanent, point_variable]
    if any(value < 0 for value in values):
        raise ValueError("A rotina simplificada de gravidade não admite ações favoráveis negativas.")
    if not (0.0 <= psi1 <= 1.0 and 0.0 <= psi2 <= 1.0):
        raise ValueError("Os fatores ψ1 e ψ2 devem estar entre 0 e 1.")
    factors = {
        "rare": 1.0,
        "frequent": psi1,
        "quasi_permanent": psi2,
        "variable_only": 1.0,
    }
    if combination not in factors:
        raise ValueError("Combinação ELS inválida.")
    factor = factors[combination]
    include_permanent = combination != "variable_only"
    return {
        "q": (q_permanent + self_weight if include_permanent else 0.0) + factor * q_variable,
        "P": (point_permanent if include_permanent else 0.0) + factor * point_variable,
        "q_permanent": q_permanent,
        "q_variable": q_variable,
        "self_weight": self_weight,
        "point_permanent": point_permanent,
        "point_variable": point_variable,
        "variable_factor": factor,
        "include_permanent": include_permanent,
        "reference": "ABNT NBR 8800:2024, 4.8.7.3 e Anexo B",
    }


def validate_material(fy: float, fu: float) -> list[str]:
    issues: list[str] = []
    if fy <= 0 or fu <= 0:
        return ["fy e fu devem ser positivos."]
    if fy > 45.0 + 1e-9:
        issues.append("fy nominal excede 45 kN/cm² (450 MPa).")
    if fu / fy < 1.15 - 1e-9:
        issues.append("A relação nominal fu/fy é inferior a 1,15.")
    return issues


def _overall_flexural_cap(W: float, fy: float, gamma_a1: float) -> float:
    return 1.50 * W * fy / gamma_a1


def _piecewise_strength(
    slenderness: float,
    lambda_p: float,
    lambda_r: float,
    plastic_or_yield: float,
    residual: float,
    critical: float,
    gamma_a1: float,
) -> tuple[float, str]:
    if slenderness <= lambda_p:
        return plastic_or_yield / gamma_a1, "plástico"
    if slenderness <= lambda_r:
        fraction = (slenderness - lambda_p) / (lambda_r - lambda_p)
        return (plastic_or_yield - (plastic_or_yield - residual) * fraction) / gamma_a1, "inelástico"
    return critical / gamma_a1, "elástico"


def flexural_strength_i(
    props: dict,
    fy: float,
    fu: float,
    E: float,
    Lb: float,
    Cb: float,
    fabrication: str,
    stiffener_spacing: float | None = None,
    flt_applicable: bool = True,
    net_tension_flange_area: float | None = None,
    gross_tension_flange_area: float | None = None,
    gamma_a1: float = GAMMA_A1,
    gamma_a2: float = GAMMA_A2,
) -> dict:
    """Resistência à flexão de seções I/H duplamente simétricas no eixo forte."""
    required = ("d", "bf", "tw", "tf", "h_clear", "Wx", "Zx", "Iy", "J", "Cw", "ry")
    missing = [name for name in required if props.get(name, 0) <= 0]
    if missing:
        raise ValueError(f"Propriedades inválidas: {', '.join(missing)}")
    if fy <= 0 or fu <= 0 or E <= 0 or Lb <= 0 or Cb <= 0:
        raise ValueError("fy, fu, E, Lb e Cb devem ser positivos.")

    d, bf, tw, tf = (props[name] for name in ("d", "bf", "tw", "tf"))
    h, W, Z = props["h_clear"], props["Wx"], props["Zx"]
    Iy, J, Cw, ry = (props[name] for name in ("Iy", "J", "Cw", "ry"))
    welded = fabrication.lower().startswith("sold")
    sigma_r = 0.30 * fy
    Mpl = Z * fy
    cap = _overall_flexural_cap(W, fy, gamma_a1)
    web_lambda = h / tw
    web_lp = 3.76 * math.sqrt(E / fy)
    web_lr = 5.70 * math.sqrt(E / fy)
    slender_web = web_lambda > web_lr
    warnings: list[str] = []
    applicability: list[str] = []
    Mr_flange = None
    Mcr_flange = None
    Mr_web = None
    M_y = None
    M_r = None
    Wxc = None
    hc = None
    Iyc = None
    Ayc = None
    ryc = None
    ltb_lp = None
    ltb_lr = None

    # FLT de alma não esbelta: alternativa de D.2.1 baseada em lambda_LT.
    if not slender_web:
        Mcr_ltb = (
            Cb
            * math.pi**2
            * E
            * Iy
            / Lb**2
            * math.sqrt((Cw / Iy) * (1.0 + 0.039 * J * Lb**2 / Cw))
        )
        lambda_lt = math.sqrt(Mpl / Mcr_ltb) if Mcr_ltb > 0 else math.inf
        if lambda_lt <= 0.4:
            chi_lt = 1.0
            ltb_regime = "plástico"
        elif lambda_lt <= 1.4:
            chi_lt = 1.0 - 0.49 * (lambda_lt - 0.4)
            ltb_regime = "inelástico"
        else:
            chi_lt = 1.0 / lambda_lt**2
            ltb_regime = "elástico"
        mrd_ltb = min(chi_lt * Mpl / gamma_a1, cap) if flt_applicable else None

        flange_lambda = bf / (2.0 * tf)
        flange_lp = 0.38 * math.sqrt(E / fy)
        kc = max(0.35, min(4.0 / math.sqrt(h / tw), 0.76))
        if welded:
            flange_lr = 0.95 * math.sqrt(E * kc / (fy - sigma_r))
            Mcr_flange = 0.90 * E * kc * W / flange_lambda**2
        else:
            flange_lr = 0.83 * math.sqrt(E / (fy - sigma_r))
            Mcr_flange = 0.69 * E * W / flange_lambda**2
        Mr_flange = (fy - sigma_r) * W
        mrd_flange, flange_regime = _piecewise_strength(
            flange_lambda, flange_lp, flange_lr, Mpl, Mr_flange, Mcr_flange, gamma_a1
        )
        mrd_flange = min(mrd_flange, cap)

        Mr_web = fy * W
        if web_lambda <= web_lp:
            mrd_web, web_regime = Mpl / gamma_a1, "plástico"
        else:
            fraction = (web_lambda - web_lp) / (web_lr - web_lp)
            mrd_web = (Mpl - (Mpl - Mr_web) * fraction) / gamma_a1
            web_regime = "inelástico"
        mrd_web = min(mrd_web, cap)
        mrd_tension = None
        kpg = None
        annex_e_limit = None
        ar = None
    else:
        # Anexo E: aplicável a perfis I/H soldados e dentro dos limites E.5.3.
        if not welded:
            applicability.append("Alma esbelta em perfil laminado fora do escopo do Anexo E.")
        a_h = math.inf if not stiffener_spacing or stiffener_spacing <= 0 else stiffener_spacing / h
        annex_e_limit = min(
            260.0,
            11.7 * math.sqrt(E / fy) if a_h <= 1.5 else 0.42 * E / fy,
        )
        if web_lambda > annex_e_limit + 1e-9:
            applicability.append(
                f"h/tw={web_lambda:.2f} excede o limite {annex_e_limit:.2f} do Anexo E."
            )
        Ac = bf * tf
        hc = d - 2.0 * tf
        ar = hc * tw / Ac
        if ar > 10.0 + 1e-9:
            applicability.append(f"ar={ar:.2f} excede 10,0 (Anexo E).")
        kpg = 1.0 - ar / (1200.0 + 300.0 * ar) * (
            hc / tw - 5.70 * math.sqrt(E / fy)
        )
        kpg = min(kpg, 1.0)
        if kpg <= 0:
            applicability.append("O fator kpg resultou não positivo.")

        Wxc = W
        M_y = kpg * fy * Wxc
        M_r = kpg * (fy - sigma_r) * Wxc
        web_segment = hc / 6.0
        Iyc = tf * bf**3 / 12.0 + web_segment * tw**3 / 12.0
        Ayc = Ac + web_segment * tw
        ryc = math.sqrt(Iyc / Ayc)
        ltb_lambda = Lb / ryc
        ltb_lp = 1.10 * math.sqrt(E / fy)
        ltb_lr = math.pi * math.sqrt(E / (fy - sigma_r))
        Mcr_ltb = Cb * kpg * math.pi**2 * E * Wxc / ltb_lambda**2
        mrd_ltb_value, ltb_regime = _piecewise_strength(
            ltb_lambda, ltb_lp, ltb_lr, M_y, M_r, Mcr_ltb, gamma_a1
        )
        mrd_ltb = min(mrd_ltb_value, cap) if flt_applicable else None
        lambda_lt = ltb_lambda
        chi_lt = None

        flange_lambda = bf / (2.0 * tf)
        flange_lp = 0.38 * math.sqrt(E / fy)
        kc = max(0.35, min(4.0 / math.sqrt(h / tw), 0.76))
        flange_lr = 0.95 * math.sqrt(E * kc / (fy - sigma_r))
        Mcr_flange = 0.90 * kpg * E * kc * Wxc / flange_lambda**2
        mrd_flange, flange_regime = _piecewise_strength(
            flange_lambda,
            flange_lp,
            flange_lr,
            M_y,
            M_r,
            Mcr_flange,
            gamma_a1,
        )
        mrd_flange = min(mrd_flange, cap)
        mrd_tension = min(fy * W / gamma_a1, cap)
        mrd_web, web_regime = mrd_tension, "Anexo E — escoamento da mesa tracionada"

    rupture_limit = None
    rupture_condition_ok = True
    Yt = 1.0 if fy / fu <= 0.8 else 1.10
    Afg = None
    Afn = None
    holes_checked = net_tension_flange_area is not None or gross_tension_flange_area is not None
    if holes_checked:
        Afg = gross_tension_flange_area or bf * tf
        Afn = net_tension_flange_area if net_tension_flange_area is not None else Afg
        if Afn <= 0 or Afg <= 0 or Afn > Afg + 1e-9:
            applicability.append("Áreas líquida/bruta da mesa tracionada inválidas.")
        else:
            rupture_condition_ok = fu * Afn >= Yt * fy * Afg
            if not rupture_condition_ok:
                rupture_limit = fu * (Afn / Afg) * W / gamma_a2

    candidates = [mrd_flange, mrd_web]
    if mrd_ltb is not None:
        candidates.append(mrd_ltb)
    if rupture_limit is not None:
        candidates.append(rupture_limit)
    mrd = min(candidates + [cap]) if not applicability else 0.0

    return {
        "Mrd": mrd,
        "Mrd_FLT": mrd_ltb,
        "Mrd_FLM": mrd_flange,
        "Mrd_FLA_or_tension": mrd_web,
        "Mrd_rupture": rupture_limit,
        "Mpl": Mpl,
        "cap_5_4_2_2": cap,
        "Mcr_FLT": Mcr_ltb,
        "Mcr_FLM": Mcr_flange,
        "Mr_FLM": Mr_flange,
        "Mr_FLA": Mr_web,
        "lambda_LT": lambda_lt,
        "chi_LT": chi_lt,
        "regime_FLT": "não aplicável — mesa comprimida contida" if not flt_applicable else ltb_regime,
        "lambda_FLM": flange_lambda,
        "lambda_p_FLM": flange_lp,
        "lambda_r_FLM": flange_lr,
        "kc": kc,
        "regime_FLM": flange_regime,
        "lambda_FLA": web_lambda,
        "lambda_p_FLA": web_lp,
        "lambda_r_FLA": web_lr,
        "regime_FLA": web_regime,
        "slender_web": slender_web,
        "kpg": kpg,
        "ar": ar,
        "annex_e_limit": annex_e_limit,
        "M_y_annex_e": M_y,
        "M_r_annex_e": M_r,
        "Wxc": Wxc,
        "hc": hc,
        "Iyc": Iyc,
        "Ayc": Ayc,
        "ryc": ryc,
        "lambda_p_LT_annex_e": ltb_lp,
        "lambda_r_LT_annex_e": ltb_lr,
        "sigma_r": sigma_r,
        "Yt": Yt,
        "holes_checked": holes_checked,
        "Afg_tension": Afg,
        "Afn_tension": Afn,
        "rupture_condition_ok": rupture_condition_ok,
        "applicability_issues": applicability,
        "warnings": warnings,
        "reference": "ABNT NBR 8800:2024, 5.4.2, Anexo D e Anexo E",
    }


def shear_strength_i(
    props: dict,
    fy: float,
    E: float,
    stiffener_spacing: float | None = None,
    stiffener_width: float | None = None,
    stiffener_thickness: float | None = None,
    stiffener_pair: bool = True,
    stiffener_welded_to_web_and_flanges: bool = False,
    gamma_a1: float = GAMMA_A1,
) -> dict:
    d, h, tw = props["d"], props["h_clear"], props["tw"]
    if min(d, h, tw, fy, E) <= 0:
        raise ValueError("Propriedades inválidas para o cálculo de cisalhamento.")
    slenderness = h / tw
    stiffener_requested = bool(stiffener_spacing and stiffener_spacing > 0)
    stiffener_checks: list[dict] = []
    stiffener_valid = False
    a_h = math.inf
    j = None
    I_st = None
    I_req = None
    slender_limit = None
    b_t = None
    one_plate_inertia = None

    if stiffener_requested:
        a = float(stiffener_spacing)
        a_h = a / h
        b = float(stiffener_width or 0.0)
        t = float(stiffener_thickness or 0.0)
        slender_limit = 0.56 * math.sqrt(E / fy)
        b_t = b / t if t > 0 else math.inf
        j = max(2.5 / a_h**2 - 2.0, 0.5)  # Errata 1:2025.
        I_req = a * tw**3 * j
        # Inércia das chapas em relação ao eixo contido no plano médio da alma.
        # Não se considera como enrijecedor a faixa vazia entre as duas chapas.
        if t > 0 and b > 0:
            plate_centroid = (tw + b) / 2.0
            one_plate_inertia = t * b**3 / 12.0 + t * b * plate_centroid**2
            I_st = (2.0 if stiffener_pair else 1.0) * one_plate_inertia
        else:
            I_st = 0.0
        stiffener_checks = [
            {"name": "soldagem", "passed": stiffener_welded_to_web_and_flanges},
            {"name": "b/t", "value": b_t, "limit": slender_limit, "passed": b_t <= slender_limit},
            {"name": "inércia", "value": I_st, "limit": I_req, "passed": I_st >= I_req},
        ]
        stiffener_valid = all(check["passed"] for check in stiffener_checks)

    if stiffener_requested and stiffener_valid and a_h <= 3.0:
        kv = 5.0 + 5.0 / a_h**2
        kv_basis = "alma com enrijecedores transversais validados"
    else:
        kv = 5.34
        kv_basis = "alma sem enrijecedores eficazes ou a/h > 3"

    lambda_p = 1.10 * math.sqrt(kv * E / fy)
    lambda_r = 1.37 * math.sqrt(kv * E / fy)
    Vpl = 0.60 * d * tw * fy
    if slenderness <= lambda_p:
        Vrd = Vpl / gamma_a1
        regime = "escoamento"
    elif slenderness <= lambda_r:
        Vrd = (lambda_p / slenderness) * Vpl / gamma_a1
        regime = "flambagem inelástica"
    else:
        Vrd = 1.24 * (lambda_p / slenderness) ** 2 * Vpl / gamma_a1
        regime = "flambagem elástica"
    return {
        "Vrd": Vrd,
        "Vpl": Vpl,
        "lambda": slenderness,
        "lambda_p": lambda_p,
        "lambda_r": lambda_r,
        "kv": kv,
        "kv_basis": kv_basis,
        "regime": regime,
        "stiffener_requested": stiffener_requested,
        "stiffener_valid": stiffener_valid,
        "stiffener_checks": stiffener_checks,
        "a_h": a_h,
        "j": j,
        "I_st": I_st,
        "I_required": I_req,
        "stiffener_width": stiffener_width,
        "stiffener_thickness": stiffener_thickness,
        "stiffener_pair": stiffener_pair,
        "stiffener_slenderness": b_t,
        "stiffener_slenderness_limit": slender_limit,
        "one_plate_inertia": one_plate_inertia,
        "reference": f"{NORMA}, 5.4.3.1; {ERRATA}",
    }


def local_compression_strength(
    props: dict,
    fy: float,
    E: float,
    bearing_length: float,
    distance_to_end: float,
    fabrication: str,
    weld_root_or_radius: float | None = None,
    lateral_unbraced_length: float | None = None,
    flange_rotation_restrained: bool = True,
    relative_lateral_movement_restrained: bool = True,
    moment_at_load: float = 0.0,
    gamma_a1: float = GAMMA_A1,
) -> dict:
    """Estados-limite locais da alma sob força transversal de compressão."""
    d, bf, tw, tf = (props[name] for name in ("d", "bf", "tw", "tf"))
    h = props["h_clear"]
    h_faces = props.get("h_faces", d - 2.0 * tf)
    if min(d, bf, tw, tf, h, bearing_length) <= 0:
        raise ValueError("Geometria inválida para forças localizadas.")
    if fabrication.lower().startswith("lam"):
        radius = max((h_faces - h) / 2.0, 0.0)
        k_extra = radius
    else:
        k_extra = max(float(weld_root_or_radius or 0.0), 0.0)
    k = tf + k_extra
    ln = bearing_length

    if distance_to_end > d:
        yielding = 1.10 * (5.0 * k + ln) * fy * tw / gamma_a1
        yielding_case = "seção interna (distância > d)"
    else:
        yielding = 1.10 * (2.5 * k + ln) * fy * tw / gamma_a1
        yielding_case = "próxima à extremidade (distância ≤ d)"

    ratio_tw_tf = (tw / tf) ** 1.5
    root_term = math.sqrt(E * fy * tf / tw)
    if distance_to_end >= d / 2.0:
        crippling = (
            0.66
            * tw**2
            / gamma_a1
            * (1.0 + 3.0 * (ln / d) * ratio_tw_tf)
            * root_term
        )
        crippling_case = "seção interna"
    elif ln / d <= 0.2:
        crippling = (
            0.33
            * tw**2
            / gamma_a1
            * (1.0 + 3.0 * (ln / d) * ratio_tw_tf)
            * root_term
        )
        crippling_case = "extremidade, ln/d ≤ 0,2"
    else:
        crippling = (
            0.33
            * tw**2
            / gamma_a1
            * (1.0 + (4.0 * ln / d - 0.2) * ratio_tw_tf)
            * root_term
        )
        crippling_case = "extremidade, ln/d > 0,2"

    sidesway = None
    sidesway_ratio = None
    sidesway_case = "não aplicável — deslocamento lateral relativo impedido"
    sidesway_limit = None
    Cr = None
    Mr = None
    kpg_local = 1.0
    if not relative_lateral_movement_restrained:
        ell = float(lateral_unbraced_length or 0.0)
        if ell <= 0:
            sidesway_case = "não verificado — comprimento destravado local não informado"
        else:
            sidesway_ratio = (h / tw) / (ell / bf)
            sidesway_limit = 2.30 if flange_rotation_restrained else 1.70
            if sidesway_ratio > sidesway_limit:
                sidesway_case = "não ocorre pelo critério geométrico de 5.7.5.3"
            else:
                # Momento de início de escoamento sem tensões residuais. Para
                # alma esbelta, o Anexo E reduz esse valor por kpg.
                web_lambda = h / tw
                web_lambda_r = 5.70 * math.sqrt(E / fy)
                if web_lambda > web_lambda_r and fabrication.lower().startswith("sold"):
                    Ac = bf * tf
                    ar = h * tw / Ac
                    kpg_local = min(
                        1.0,
                        1.0 - ar / (1200.0 + 300.0 * ar)
                        * (h / tw - web_lambda_r),
                    )
                Mr = max(kpg_local, 0.0) * fy * props["Wx"]
                Cr = (32.0 if abs(moment_at_load) < Mr else 16.0) * E
                base = Cr * tw**3 * tf / (gamma_a1 * h**2)
                if flange_rotation_restrained:
                    sidesway = base * (0.94 + 0.37 * sidesway_ratio**3)
                    sidesway_case = "rotação da mesa impedida"
                else:
                    sidesway = base * (0.37 * sidesway_ratio**3)
                    sidesway_case = "rotação da mesa não impedida"

    values = [yielding, crippling] + ([sidesway] if sidesway is not None else [])
    return {
        "FRd": min(values),
        "yielding_FRd": yielding,
        "yielding_case": yielding_case,
        "crippling_FRd": crippling,
        "crippling_case": crippling_case,
        "sidesway_FRd": sidesway,
        "sidesway_ratio": sidesway_ratio,
        "sidesway_limit": sidesway_limit,
        "sidesway_case": sidesway_case,
        "Cr": Cr,
        "Mr": Mr,
        "kpg_local": kpg_local,
        "k": k,
        "bearing_length": ln,
        "distance_to_end": distance_to_end,
        "reference": f"{NORMA}, 5.7.3 a 5.7.5",
    }


def local_flange_bending_strength(
    tf: float, fy: float, distance_to_end: float, gamma_a1: float = GAMMA_A1
) -> float:
    resistance = 6.25 * tf**2 * fy / gamma_a1
    if distance_to_end < 10.0 * tf:
        resistance *= 0.5
    return resistance


def deflection_limit(
    support: str,
    length: float,
    divisor: float,
    absolute_limit: float | None = None,
) -> float:
    normalized = SUPPORT_ALIASES.get(support)
    if normalized is None or length <= 0 or divisor <= 0:
        raise ValueError("Dados inválidos para o limite de deslocamento.")
    reference_length = 2.0 * length if normalized == "cantilever" else length
    limit = reference_length / divisor
    return min(limit, absolute_limit) if absolute_limit and absolute_limit > 0 else limit


def overall_status(statuses: Iterable[str]) -> str:
    values = list(statuses)
    # Uma reprovação comprovada é conclusiva; pendências só governam quando
    # nenhuma verificação já demonstrou insuficiência.
    if any(value == "REPROVADO" for value in values):
        return "REPROVADO"
    if any(value == "NÃO VERIFICADO" for value in values):
        return "NÃO VERIFICADO"
    if all(value in {"APROVADO", "N/A"} for value in values):
        return "APROVADO"
    return "NÃO VERIFICADO"
