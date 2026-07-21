"""Diagramas SVG auditáveis para o memorial estrutural.

As funções deste módulo não recalculam a análise da viga. Elas consomem os
resultados do núcleo (reações, esforços e deslocamentos) e os transformam em
representações vetoriais responsivas, adequadas ao navegador e à impressão.
"""

from __future__ import annotations

import html
import math


SVG_WIDTH = 720.0
PLOT_LEFT = 58.0
PLOT_RIGHT = 682.0
PLOT_WIDTH = PLOT_RIGHT - PLOT_LEFT


def _esc(value):
    return html.escape(str(value), quote=True)


def _num(value, digits=3):
    if value is None or not math.isfinite(float(value)):
        return "N/A"
    number = round(float(value), digits)
    if number == 0:
        number = 0.0
    if digits <= 0:
        return f"{number:.0f}"
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def _x_px(value, length, left=PLOT_LEFT, width=PLOT_WIDTH):
    if length <= 0:
        return left
    ratio = min(max(float(value) / float(length), 0.0), 1.0)
    return left + ratio * width


def _support_name(support):
    return {
        "simply_supported": "biapoiada",
        "cantilever": "balanço",
        "fixed_fixed": "biengastada",
        "propped_cantilever": "engastada–apoiada",
    }.get(support, str(support))


def _marker_defs(uid, color="#fbbf24"):
    return f"""
    <defs>
      <marker id="{uid}-arrow-load" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
        <path d="M0,0 L8,4 L0,8 Z" fill="#fb7185"/>
      </marker>
      <marker id="{uid}-arrow-reaction" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
        <path d="M0,0 L8,4 L0,8 Z" fill="#38bdf8"/>
      </marker>
      <marker id="{uid}-arrow-dim" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto-start-reverse">
        <path d="M0,3.5 L7,0 L7,7 Z" fill="#94a3b8"/>
      </marker>
      <linearGradient id="{uid}-area" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="{color}" stop-opacity="0.42"/>
        <stop offset="100%" stop-color="{color}" stop-opacity="0.04"/>
      </linearGradient>
      <pattern id="{uid}-hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
        <line x1="0" y1="0" x2="0" y2="8" stroke="#64748b" stroke-width="2"/>
      </pattern>
    </defs>"""


def _svg_open(uid, height, title, description, color="#fbbf24"):
    return f"""
    <svg class="engineering-svg" viewBox="0 0 720 {height}" role="img"
         aria-labelledby="{uid}-title {uid}-desc" preserveAspectRatio="xMidYMid meet">
      <title id="{uid}-title">{_esc(title)}</title>
      <desc id="{uid}-desc">{_esc(description)}</desc>
      {_marker_defs(uid, color)}
    """


def _figure(kind, title, kicker, caption, svg, metrics=(), attributes=None):
    attrs = {"data-visual": kind}
    attrs.update(attributes or {})
    attr_html = " ".join(f'{_esc(key)}="{_esc(value)}"' for key, value in attrs.items())
    metric_html = "".join(
        f'<div class="visual-metric"><span>{_esc(label)}</span><strong>{_esc(value)}</strong></div>'
        for label, value in metrics
    )
    return f"""
    <figure class="engineering-visual" {attr_html}>
      <div class="visual-head">
        <div><span>{_esc(kicker)}</span><h5>{_esc(title)}</h5></div>
        <small>Representação vetorial</small>
      </div>
      <div class="visual-svg-wrap">{svg}</div>
      {f'<div class="visual-metrics">{metric_html}</div>' if metric_html else ''}
      <figcaption>{_esc(caption)}</figcaption>
    </figure>"""


def _pin_support(x, beam_y, roller=False):
    roller_svg = ""
    if roller:
        roller_svg = (
            f'<circle cx="{x-7:.1f}" cy="{beam_y+31:.1f}" r="4" class="support-fill"/>'
            f'<circle cx="{x+7:.1f}" cy="{beam_y+31:.1f}" r="4" class="support-fill"/>'
        )
    return f"""
      <path d="M{x:.1f},{beam_y+3:.1f} L{x-18:.1f},{beam_y+27:.1f} L{x+18:.1f},{beam_y+27:.1f} Z" class="support-shape"/>
      {roller_svg}
      <line x1="{x-25:.1f}" y1="{beam_y+36:.1f}" x2="{x+25:.1f}" y2="{beam_y+36:.1f}" class="support-ground"/>
    """


def _fixed_support(x, beam_y, side, uid):
    wall_x = x - 5 if side == "left" else x + 5
    rect_x = wall_x - 12 if side == "left" else wall_x
    return f"""
      <line x1="{wall_x:.1f}" y1="{beam_y-39:.1f}" x2="{wall_x:.1f}" y2="{beam_y+39:.1f}" class="support-wall"/>
      <rect x="{rect_x:.1f}" y="{beam_y-39:.1f}" width="12" height="78" fill="url(#{uid}-hatch)"/>
    """


def beam_model_visual(response):
    """Esquema de vinculação, ações de cálculo e reações."""
    uid = "beam-model"
    L = response.length
    x0, x1, beam_y = PLOT_LEFT, PLOT_RIGHT, 126.0
    parts = [
        _svg_open(
            uid, 286, "Modelo estrutural e carregamentos de cálculo",
            "Viga com apoios, carga distribuída, força pontual, reações e cotas longitudinais.",
        ),
        '<g class="engineering-drawing">',
        f'<line x1="{x0}" y1="{beam_y}" x2="{x1}" y2="{beam_y}" class="beam-line"/>',
    ]

    if response.q > 0:
        parts.append(f'<line x1="{x0}" y1="43" x2="{x1}" y2="43" class="load-spine"/>')
        for index in range(13):
            x = x0 + PLOT_WIDTH * index / 12.0
            parts.append(
                f'<line x1="{x:.1f}" y1="43" x2="{x:.1f}" y2="106" class="load-arrow" marker-end="url(#{uid}-arrow-load)"/>'
            )
        q_on_right = response.point_load > 0 and response.point_position < 0.45 * L
        q_label_x = x1 if q_on_right else x0
        q_anchor = "end" if q_on_right else "start"
        parts.append(
            f'<text x="{q_label_x:.1f}" y="28" text-anchor="{q_anchor}" class="svg-label load-label">q<tspan baseline-shift="sub">d</tspan> = {_num(response.q*100)} kN/m</text>'
        )

    if response.point_load > 0:
        xp = _x_px(response.point_position, L)
        anchor = "end" if xp > 585 else "start" if xp < 135 else "middle"
        label_x = xp - 9 if anchor == "end" else xp + 9 if anchor == "start" else xp
        parts.extend((
            f'<line x1="{xp:.1f}" y1="28" x2="{xp:.1f}" y2="108" class="point-arrow" marker-end="url(#{uid}-arrow-load)"/>',
            f'<text x="{label_x:.1f}" y="22" text-anchor="{anchor}" class="svg-label load-label">P<tspan baseline-shift="sub">d</tspan> = {_num(response.point_load)} kN</text>',
            f'<line x1="{xp:.1f}" y1="132" x2="{xp:.1f}" y2="242" class="guide-line"/>',
        ))

    support = response.support
    if support == "simply_supported":
        parts.extend((_pin_support(x0, beam_y), _pin_support(x1, beam_y, roller=True)))
    elif support == "cantilever":
        parts.append(_fixed_support(x0, beam_y, "left", uid))
    elif support == "fixed_fixed":
        parts.extend((_fixed_support(x0, beam_y, "left", uid), _fixed_support(x1, beam_y, "right", uid)))
    elif support == "propped_cantilever":
        parts.extend((_fixed_support(x0, beam_y, "left", uid), _pin_support(x1, beam_y, roller=True)))

    if abs(response.reaction_left) > 1e-12:
        parts.extend((
            f'<line x1="{x0}" y1="213" x2="{x0}" y2="151" class="reaction-arrow" marker-end="url(#{uid}-arrow-reaction)"/>',
            f'<text x="{x0+10}" y="209" class="svg-label reaction-label">R<tspan baseline-shift="sub">A</tspan> = {_num(response.reaction_left)} kN</text>',
        ))
    if abs(response.reaction_right) > 1e-12:
        parts.extend((
            f'<line x1="{x1}" y1="213" x2="{x1}" y2="151" class="reaction-arrow" marker-end="url(#{uid}-arrow-reaction)"/>',
            f'<text x="{x1-10}" y="209" text-anchor="end" class="svg-label reaction-label">R<tspan baseline-shift="sub">B</tspan> = {_num(response.reaction_right)} kN</text>',
        ))

    parts.extend((
        f'<line x1="{x0}" y1="252" x2="{x1}" y2="252" class="dimension-line" marker-start="url(#{uid}-arrow-dim)" marker-end="url(#{uid}-arrow-dim)"/>',
        f'<text x="{(x0+x1)/2:.1f}" y="274" class="svg-label dimension-label">L = {_num(L/100)} m</text>',
    ))
    if response.point_load > 0:
        xp = _x_px(response.point_position, L)
        parts.extend((
            f'<line x1="{x0}" y1="226" x2="{xp:.1f}" y2="226" class="dimension-line" marker-start="url(#{uid}-arrow-dim)" marker-end="url(#{uid}-arrow-dim)"/>',
            f'<text x="{(x0+xp)/2:.1f}" y="220" class="svg-label dimension-label">a = {_num(response.point_position/100)} m</text>',
        ))
    parts.extend((
        f'<text x="{x0}" y="119" class="svg-node-label">A</text>',
        f'<text x="{x1}" y="119" text-anchor="end" class="svg-node-label">B</text>',
        '</g></svg>',
    ))
    metrics = (
        ("Vinculação", _support_name(response.support)),
        ("Momento em A", f"{_num(response.moment_left/100)} kN·m"),
        ("Momento em B", f"{_num(response.moment_right/100)} kN·m"),
    )
    return _figure(
        "beam-model", "Modelo estrutural e carregamentos", "ELU · equilíbrio",
        "Setas vermelhas representam ações de cálculo; setas azuis representam reações. Cotas longitudinais em escala relativa ao vão.",
        "".join(parts), metrics,
        {"data-length-cm": _num(L), "data-point-position-cm": _num(response.point_position)},
    )


def _sample_curve(xs, ys, max_points=181, required_x=()):
    if not xs:
        return []
    size = len(xs)
    stride = max(1, math.ceil(size / max_points))
    indices = set(range(0, size, stride)) | {0, size - 1}
    for target in required_x:
        indices.add(min(range(size), key=lambda idx: abs(xs[idx] - target)))
    return [(float(xs[idx]), float(ys[idx])) for idx in sorted(indices)]


def _chart_svg(
    uid, title, description, points, length, axis_label, value_unit,
    color, critical, guide_x=None, markers=(), positive_down=False,
    convention_label="",
):
    height = 286.0
    top, bottom = 38.0, 218.0
    values = [value for _, value in points] or [0.0]
    y_min, y_max = min(min(values), 0.0), max(max(values), 0.0)
    span = y_max - y_min
    if span <= 1e-12:
        y_min, y_max, span = -1.0, 1.0, 2.0
    pad = span * 0.14
    y_min -= pad
    y_max += pad

    def y_px(value):
        normalized = (value - y_min) / (y_max - y_min)
        if positive_down:
            return top + normalized * (bottom - top)
        return bottom - normalized * (bottom - top)

    zero_y = y_px(0.0)
    coords = [(_x_px(x, length), y_px(value)) for x, value in points]
    path = " ".join(("M" if index == 0 else "L") + f"{x:.2f},{y:.2f}" for index, (x, y) in enumerate(coords))
    area = ""
    if coords:
        area = f'M{coords[0][0]:.2f},{zero_y:.2f} ' + " ".join(
            ("L" if index else "L") + f"{x:.2f},{y:.2f}" for index, (x, y) in enumerate(coords)
        ) + f' L{coords[-1][0]:.2f},{zero_y:.2f} Z'
    grid = []
    for ratio in (0.0, 0.25, 0.5, 0.75, 1.0):
        x = PLOT_LEFT + ratio * PLOT_WIDTH
        grid.extend((
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" class="chart-grid"/>',
            f'<text x="{x:.1f}" y="245" class="svg-axis-label">{_num(length*ratio/100,2)}</text>',
        ))
    critical_x, critical_value = critical
    cx, cy = _x_px(critical_x, length), y_px(critical_value)
    anchor = "end" if cx > 560 else "start"
    label_x = cx - 10 if anchor == "end" else cx + 10
    extra_markers = []
    for marker in markers:
        mx = _x_px(marker[0], length)
        my = y_px(marker[1])
        extra_markers.append(
            f'<g class="chart-marker secondary"><circle cx="{mx:.1f}" cy="{my:.1f}" r="4"/>'
            f'<text x="{mx:.1f}" y="{top-9:.1f}" class="svg-marker-label">{_esc(marker[2])}</text>'
            f'<line x1="{mx:.1f}" y1="{top}" x2="{mx:.1f}" y2="{bottom}" class="guide-line"/></g>'
        )
    guide = ""
    if guide_x is not None:
        gx = _x_px(guide_x, length)
        guide = (
            f'<line x1="{gx:.1f}" y1="{top}" x2="{gx:.1f}" y2="{bottom}" class="load-guide"/>'
            f'<text x="{gx:.1f}" y="{top-9:.1f}" class="svg-marker-label load-text">P em {_num(guide_x/100,2)} m</text>'
        )
    svg = [
        _svg_open(uid, height, title, description, color),
        '<g class="engineering-chart">',
        *grid,
        f'<line x1="{PLOT_LEFT}" y1="{zero_y:.2f}" x2="{PLOT_RIGHT}" y2="{zero_y:.2f}" class="chart-zero"/>',
        f'<path d="{area}" fill="url(#{uid}-area)"/>',
        f'<path d="{path}" class="chart-curve" style="stroke:{color}"/>',
        guide,
        *extra_markers,
        f'<g class="chart-marker"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" style="fill:{color}"/>'
        f'<text x="{label_x:.1f}" y="{cy-12:.1f}" text-anchor="{anchor}" class="svg-critical-label">{_num(critical_value)} {value_unit}</text>'
        f'<text x="{label_x:.1f}" y="{cy+9:.1f}" text-anchor="{anchor}" class="svg-critical-sub">x = {_num(critical_x/100)} m</text></g>',
        f'<text x="{PLOT_LEFT}" y="20" class="svg-axis-title">{_esc(axis_label)}</text>',
        (
            f'<text x="{PLOT_LEFT}" y="271" text-anchor="start" '
            f'class="svg-convention-label">{_esc(convention_label)}</text>'
            if convention_label else ""
        ),
        f'<text x="{PLOT_RIGHT}" y="271" text-anchor="end" class="svg-axis-title">x (m)</text>',
        '</g></svg>',
    ]
    return "".join(svg)


def effort_diagrams_visual(response):
    """Diagramas de cortante e momento obtidos da resposta ELU."""
    L, P, a, q = response.length, response.point_load, response.point_position, response.q
    shear_points = []
    divisions = 180
    for index in range(divisions + 1):
        x = L * index / divisions
        if P > 0 and math.isclose(x, a, abs_tol=L/divisions/2):
            continue
        value = response.reaction_left - q * x - (P if x > a else 0.0)
        shear_points.append((x, value))
    if P > 0:
        left_value = response.reaction_left - q * a
        shear_points.extend(((a, left_value), (a, left_value - P)))
        shear_points.sort(key=lambda pair: (pair[0], -pair[1]))
    shear_critical = max(shear_points, key=lambda pair: abs(pair[1]))

    moment_xs = [L * index / divisions for index in range(divisions + 1)]
    moment_xs.extend((a, response.max_moment_position))
    moment_xs = sorted(set(moment_xs))
    moment_points = [(x, response.moment_at(x) / 100.0) for x in moment_xs]
    moment_critical = (
        response.max_moment_position,
        response.moment_at(response.max_moment_position) / 100.0,
    )
    guide = a if P > 0 else None
    shear_svg = _chart_svg(
        "shear-diagram", "Diagrama de força cortante", "Força cortante de cálculo ao longo do vão.",
        shear_points, L, "Vd (kN)", "kN", "#a78bfa", shear_critical, guide,
        convention_label="+V acima · −V abaixo",
    )
    moment_svg = _chart_svg(
        "moment-diagram", "Diagrama de momento fletor", "Momento fletor de cálculo ao longo do vão.",
        moment_points, L, "Md (kN·m)", "kN·m", "#fbbf24", moment_critical, guide,
        positive_down=True, convention_label="+M abaixo · −M acima",
    )
    return '<div class="engineering-visual-stack">' + _figure(
        "shear-diagram", "Diagrama de força cortante", "ELU · Vd(x)",
        "O salto vertical coincide com a força pontual. Convenção algébrica: cortante positivo acima e negativo abaixo da linha de referência.",
        shear_svg,
        (("VSd,max", f"{_num(response.max_shear)} kN"), ("Seção crítica", f"x = {_num(shear_critical[0]/100)} m")),
        {"data-critical-x-cm": _num(shear_critical[0]), "data-critical-value": _num(shear_critical[1]), "data-positive-direction": "up"},
    ) + _figure(
        "moment-diagram", "Diagrama de momento fletor", "ELU · Md(x)",
        "Convenção brasileira de traçado no lado tracionado: momento sagente positivo abaixo da linha da viga e momento negativo acima.",
        moment_svg,
        (("MSd,max", f"{_num(response.max_moment/100)} kN·m"), ("Seção crítica", f"x = {_num(response.max_moment_position/100)} m")),
        {"data-critical-x-cm": _num(response.max_moment_position), "data-critical-value": _num(moment_critical[1]), "data-positive-direction": "down"},
    ) + '</div>'


def cb_diagram_visual(response, info):
    """Diagrama do trecho Lb com os pontos empregados no cálculo de Cb."""
    if response is None or not info:
        return ""
    x0, lb = info["segment_start"], info["Lb"]
    x1 = x0 + lb
    divisions = 180
    xs = [x0 + lb * index / divisions for index in range(divisions + 1)]
    points = [(x - x0, response.moment_at(x) / 100.0) for x in xs]
    critical_global = info.get("xMmax", max(xs, key=lambda x: abs(response.moment_at(x))))
    critical = (critical_global - x0, response.moment_at(critical_global) / 100.0)
    marker_data = (
        (lb/4.0, response.moment_at(x0+lb/4.0)/100.0, f"MA = {_num(info['MA']/100)}"),
        (lb/2.0, response.moment_at(x0+lb/2.0)/100.0, f"MB = {_num(info['MB']/100)}"),
        (3*lb/4.0, response.moment_at(x0+3*lb/4.0)/100.0, f"MC = {_num(info['MC']/100)}"),
    )
    svg = _chart_svg(
        "cb-diagram", "Momento no trecho destravado Lb",
        "Diagrama de momento entre as contenções laterais, com marcação dos quartos do trecho.",
        points, lb, "M (kN·m)", "kN·m", "#22d3ee", critical, None, marker_data,
        positive_down=True, convention_label="+M abaixo · −M acima",
    )
    return _figure(
        "cb-diagram", "Gradiente de momento no trecho destravado", "ESTABILIDADE · Cb",
        "MA, MB e MC são os momentos em módulo nos quartos de Lb. A curva conserva o sinal e usa a convenção brasileira: sagente positivo abaixo da linha de referência.",
        svg,
        (
            ("Trecho", f"{_num(x0/100)} a {_num(x1/100)} m"),
            ("Lb", f"{_num(lb/100)} m"),
            ("Cb", _num(info["Cb"], 4)),
        ),
        {"data-lb-cm": _num(lb), "data-cb": _num(info["Cb"], 4), "data-positive-direction": "down"},
    )


def local_action_visual(check, length):
    """Esquema compacto da posição e da faixa de atuação da força localizada."""
    uid = "local-" + "-".join(str(check.get("name", "forca")).lower().split())
    position = float(check.get("position", 0.0))
    bearing = float(check.get("bearing_length", check["details"].get("bearing_length", 0.0)))
    distance = float(check["details"].get("distance_to_end", min(position, length-position)))
    xp = _x_px(position, length)
    patch_width = max(14.0, bearing / max(length, 1.0) * PLOT_WIDTH)
    is_support = "apoio" in check.get("name", "").lower()
    arrow_y1, arrow_y2 = (181.0, 121.0) if is_support else (32.0, 101.0)
    marker = f"url(#{uid}-arrow-reaction)" if is_support else f"url(#{uid}-arrow-load)"
    arrow_class = "reaction-arrow" if is_support else "point-arrow"
    near_x = PLOT_LEFT if position <= length/2 else PLOT_RIGHT
    if is_support:
        force_anchor = "start" if position <= length/2 else "end"
        force_x = xp + 14.0 if force_anchor == "start" else xp - 14.0
        bearing_anchor = force_anchor
        bearing_label_x = xp + 28.0 if bearing_anchor == "start" else xp - 28.0
        force_label = (
            f'<text x="{force_x:.1f}" y="181" text-anchor="{force_anchor}" class="svg-label reaction-label-local">'
            f'F<tspan baseline-shift="sub">Sd</tspan> = {_num(check["demand"])} kN</text>'
        )
    else:
        bearing_anchor = "middle"
        bearing_label_x = xp
        force_label = (
            f'<text x="{xp:.1f}" y="24" class="svg-label load-label">'
            f'F<tspan baseline-shift="sub">Sd</tspan> = {_num(check["demand"])} kN</text>'
        )
    if distance <= 1e-9:
        distance_graphic = (
            f'<text x="{(PLOT_LEFT+PLOT_RIGHT)/2:.1f}" y="219" class="svg-label dimension-label">'
            f'força junto à extremidade · distância = {_num(distance)} cm</text>'
        )
    else:
        distance_graphic = (
            f'<line x1="{near_x:.1f}" y1="198" x2="{xp:.1f}" y2="198" class="dimension-line" '
            f'marker-start="url(#{uid}-arrow-dim)" marker-end="url(#{uid}-arrow-dim)"/>'
            f'<text x="{(near_x+xp)/2:.1f}" y="219" class="svg-label dimension-label">'
            f'distância à extremidade = {_num(distance)} cm</text>'
        )
    svg = [
        _svg_open(uid, 232, f"Detalhe de {check['name']}", "Posição da força localizada, comprimento de atuação e distância à extremidade."),
        '<g class="engineering-drawing">',
        f'<line x1="{PLOT_LEFT}" y1="112" x2="{PLOT_RIGHT}" y2="112" class="beam-line"/>',
        f'<rect x="{xp-patch_width/2:.1f}" y="103" width="{patch_width:.1f}" height="18" rx="3" class="bearing-patch"/>',
        f'<line x1="{xp:.1f}" y1="{arrow_y1}" x2="{xp:.1f}" y2="{arrow_y2}" class="{arrow_class}" marker-end="{marker}"/>',
        force_label,
        f'<line x1="{xp-patch_width/2:.1f}" y1="146" x2="{xp+patch_width/2:.1f}" y2="146" class="dimension-line" marker-start="url(#{uid}-arrow-dim)" marker-end="url(#{uid}-arrow-dim)"/>',
        f'<text x="{bearing_label_x:.1f}" y="166" style="text-anchor:{bearing_anchor}" class="svg-label dimension-label">ℓn = {_num(bearing)} cm</text>',
        distance_graphic,
        '</g></svg>',
    ]
    return _figure(
        "local-action", f"Detalhe da força localizada — {check['name']}", "FORÇA LOCALIZADA",
        "A faixa destacada representa o comprimento de atuação informado; o desenho longitudinal usa escala relativa ao vão.",
        "".join(svg),
        (
            ("Posição", f"x = {_num(position/100)} m"),
            ("Demanda", f"{_num(check['demand'])} kN"),
            ("Resistência", f"{_num(check['resistance'])} kN"),
        ),
        {"data-position-cm": _num(position), "data-bearing-cm": _num(bearing)},
    )


def deflection_diagram_visual(response, deflection_limit):
    """Linha elástica ELS com posição da carga e da flecha máxima."""
    uid = "deflection-diagram"
    L = response.length
    pairs = _sample_curve(
        list(response.x), [abs(value) for value in response.deflections],
        required_x=(response.max_deflection_position, response.point_position),
    )
    top_y, max_depth = 78.0, 120.0
    scale = max(response.max_deflection, 1e-12)
    coords = [(_x_px(x, L), top_y + value / scale * max_depth) for x, value in pairs]
    path = " ".join(("M" if index == 0 else "L") + f"{x:.2f},{y:.2f}" for index, (x, y) in enumerate(coords))
    area = f'M{PLOT_LEFT},{top_y} ' + " ".join(f'L{x:.2f},{y:.2f}' for x, y in coords) + f' L{PLOT_RIGHT},{top_y} Z'
    cx = _x_px(response.max_deflection_position, L)
    cy = top_y + max_depth
    guide = ""
    if response.point_load > 0:
        gx = _x_px(response.point_position, L)
        guide = (
            f'<line x1="{gx:.1f}" y1="29" x2="{gx:.1f}" y2="214" class="load-guide"/>'
            f'<text x="{gx:.1f}" y="22" class="svg-marker-label load-text">P em x = {_num(response.point_position/100)} m</text>'
        )
    svg = [
        _svg_open(uid, 276, "Linha elástica e flecha máxima", "Deslocamento vertical ao longo da viga, com escala vertical ampliada.", "#38bdf8"),
        '<g class="engineering-chart">',
        f'<line x1="{PLOT_LEFT}" y1="{top_y}" x2="{PLOT_RIGHT}" y2="{top_y}" class="beam-datum"/>',
        f'<path d="{area}" fill="url(#{uid}-area)"/>',
        f'<path d="{path}" class="deflection-curve"/>',
        guide,
        f'<line x1="{cx:.1f}" y1="{top_y}" x2="{cx:.1f}" y2="{cy:.1f}" class="critical-guide"/>',
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" class="deflection-marker"><title>Flecha máxima em x = {_num(response.max_deflection_position/100)} m</title></circle>',
        f'<text x="{cx:.1f}" y="{cy+23:.1f}" class="svg-critical-label">δmax = {_num(response.max_deflection,4)} cm</text>',
        f'<text x="{cx:.1f}" y="{cy+42:.1f}" class="svg-critical-sub">xδ = {_num(response.max_deflection_position/100)} m</text>',
        f'<text x="{PLOT_LEFT}" y="64" class="svg-node-label">A</text>',
        f'<text x="{PLOT_RIGHT}" y="64" text-anchor="end" class="svg-node-label">B</text>',
        f'<text x="{PLOT_RIGHT}" y="260" text-anchor="end" class="svg-axis-title">deformação vertical ampliada</text>',
        '</g></svg>',
    ]
    utilization = response.max_deflection / deflection_limit * 100.0 if deflection_limit > 0 else math.inf
    status = "ATENDE" if utilization <= 100.0 else "NÃO ATENDE"
    return _figure(
        "deflection-diagram", "Linha elástica e posição da flecha máxima", "ELS · v(x)",
        "A escala vertical é ampliada para leitura e não representa a deformada geométrica real. A posição da força e a posição da flecha máxima são independentes.",
        "".join(svg),
        (
            ("Flecha máxima", f"{_num(response.max_deflection,4)} cm"),
            ("Posição xδ", f"{_num(response.max_deflection_position/100)} m"),
            ("Limite", f"{_num(deflection_limit,4)} cm"),
            ("Utilização", f"{_num(utilization,1)}% · {status}"),
        ),
        {
            "data-critical-x-cm": _num(response.max_deflection_position),
            "data-critical-value": _num(response.max_deflection, 4),
            "data-limit-cm": _num(deflection_limit, 4),
        },
    )
