import unittest
import re
import numpy as np

from calculos_nbr8800_2024 import analyze_beam
from main import compact_number, perform_all_checks
from memorial_diagrams import deflection_diagram_visual, effort_diagrams_visual


class DetailedMemorialTests(unittest.TestCase):
    def setUp(self):
        self.props = {
            "d": 50.0, "bf": 20.0, "tw": 0.8, "tf": 1.2,
            "h_faces": 47.6, "h_clear": 45.0,
            "Area": 80.0, "Ix": 25_000.0, "Wx": 1_000.0,
            "Zx": 1_150.0, "Iy": 600.0, "J": 20.0,
            "Cw": 300_000.0, "ry": 2.5, "Peso": 62.8,
        }

    def _run(self, props=None, fabrication="Laminado", input_mode="Calcular a partir de Cargas na Viga", use_stiffeners=False, **overrides):
        support_type = overrides.pop("support_type", "Bi-apoiada")
        options = dict(
            q_g_kn_cm=0.03, q_q_kn_cm=0.06, p_g_kn=0.0, p_q_kn=10.0,
            p_pos_cm=250.0, include_self_weight=True,
            gamma_g=1.50, gamma_q=1.50, gamma_self_weight=1.25,
            els_combination="rare", psi1=0.6, psi2=0.4,
            cb_modo_auto=True, lb_start_cm=0.0,
            bearing_left_cm=10.0, bearing_right_cm=10.0, point_bearing_cm=10.0,
            support_relative_lateral_restrained=True,
            point_relative_lateral_restrained=True,
            loaded_flange_rotation_restrained=True,
            larg_esq_cm=200.0, larg_dir_cm=200.0,
            larg_inf_total_m=2.0, g_area=1.5, q_area=3.0,
            scope_notes=["Viga de teste."], unsupported_reasons=[],
        )
        options.update(overrides)
        results = perform_all_checks(
            props or self.props, 34.5, 300.0, 1.0, 500.0,
            10_000.0 if input_mode != "Calcular a partir de Cargas na Viga" else 0.0,
            50.0 if input_mode != "Calcular a partir de Cargas na Viga" else 0.0,
            0.05, (10.0, 250.0), support_type, input_mode,
            fabrication, use_stiffeners, 100.0, 250.0, {}, 20_000.0,
            detalhado=True, fu_aco=45.0,
            **options,
        )
        return results[-1]

    def test_standard_memorial_exposes_formulas_substitution_and_decisions(self):
        memorial = self._run()
        for expected in (
            "MEMORIAL AUDITÁVEL", "Equações, verificações e decisões normativas",
            "Funções de cortante e momento", "Flambagem lateral com torção",
            "Resistência da alma ao cisalhamento", "Linha elástica",
            "Leitura técnica", "STATUS GLOBAL", "Fundamentação e variáveis",
            "Dicionário de símbolos", "Regime inelástico ou semicompacto",
            "Equação inelástica — Flambagem lateral com torção",
        ):
            self.assertIn(expected, memorial)
        self.assertGreater(memorial.count("calc-step"), 12)
        self.assertGreaterEqual(memorial.count('class="theory-panel"'), 6)
        self.assertEqual(memorial.count('class="step-theory-panel"'), memorial.count('class="calc-step"'))
        self.assertGreater(memorial.count(r"\begin{aligned}"), 12)
        self.assertEqual(memorial.count('class="formula-chain"'), memorial.count('class="calc-step"'))
        self.assertNotIn('class="equation-pair"', memorial)
        self.assertGreater(memorial.count(r"\Rightarrow"), memorial.count('class="calc-step"'))
        self.assertIn(r"\cdot", memorial)
        self.assertIn(r"\frac{q\cdot L}{2}", memorial)
        self.assertNotIn(r"qL/2", memorial)
        self.assertNotIn(r"\times", memorial)
        self.assertNotIn("1.50(", memorial)
        self.assertNotIn("∞", memorial)
        self.assertNotIn("Equação simbólica", memorial)
        self.assertNotIn("Substituição numérica</div>", memorial)
        self.assertNotIn("Simbólica", memorial)
        self.assertNotIn("substituição numérica", memorial)
        self.assertNotIn("Desenvolvimento do cálculo", memorial)
        self.assertNotIn("equation-caption", memorial)
        self.assertNotIn("S" + "NR", memorial.upper())
        self.assertIn(r"F_{Rd}=\min\left\{\begin{gathered}", memorial)
        self.assertIn(r"\text{escoamento local}", memorial)
        self.assertNotIn(r"F_{Rd}=\min(escoamento", memorial)
        self.assertIn(r"M_{cr}\,[kN\!\cdot\!m]=\frac{1}{100}\cdot\frac{C_b\cdot\pi^2\cdot E\cdot I_y}{L_b^2}\cdot\sqrt{\frac{C_w}{I_y}", memorial)
        self.assertIn(r"F_{Rd,cr}=\frac{0.66\cdot t_w^2}{\gamma_{a1}}", memorial)
        self.assertIn(r"\frac{5\cdot q_s\cdot L^4}{384\cdot E\cdot I_x}", memorial)
        self.assertIn(r"\frac{P_s\cdot L^3}{48\cdot E\cdot I_x}", memorial)
        self.assertIn(r"x_\delta=\frac{L}{2}", memorial)
        self.assertNotIn(r"E\cdot I_x\cdot v(x)=C_1\cdot x", memorial)
        self.assertNotIn(r"C_1", memorial)
        for invented_helper in (
            r"\Phi_t", r"\Phi_w", r"\Phi_{cr}", r"\Psi_{cr}",
            r"\alpha_f", r"M_{n,FLM}", r"\alpha_w", r"M_{n,FLA}",
            r"\alpha_{LT}", r"M_{n,FLT}", r"T_C", r"S_1",
        ):
            self.assertNotIn(invented_helper, memorial)
        for item_reference in (
            "D.2.8-a", "D.2.1 (procedimento alternativo)", "D.2.2",
            "5.4.3.1.1", "5.7.3.2", "5.7.4.2", "5.7.5.1",
            "B.2.1 a B.2.4", "Tabela B.1",
        ):
            self.assertIn(item_reference, memorial)
        chain_math = "".join(re.findall(r'class="formula-chain">\$\$(.*?)\$\$', memorial, re.S))
        self.assertNotIn(r"\quad;\quad", chain_math)
        self.assertNotIn(r"C_1", chain_math)
        self.assertNotIn(r"\begin{cases}", chain_math)
        for notation in (r"kN/m", r"\mathrm{N/A}", "FLA/mesa"):
            chain_math = chain_math.replace(notation, "")
        self.assertNotIn("/", chain_math)

    def test_manual_memorial_declares_missing_analysis_instead_of_inventing_it(self):
        memorial = self._run(input_mode="Inserir Esforços Manualmente")
        self.assertIn("Esforços informados", memorial)
        self.assertIn("nenhum diagrama é inventado", memorial)
        self.assertIn("Não calculado", memorial)

    def test_slender_welded_profile_documents_annex_e(self):
        props = dict(self.props)
        props.update(
            d=124.0, bf=30.0, tw=0.6, tf=2.0,
            h_faces=120.0, h_clear=120.0,
            Area=180.0, Ix=186_000.0, Wx=3_000.0, Zx=3_400.0,
            Iy=4_500.0, J=50.0, Cw=2_000_000.0, ry=3.0, Peso=141.3,
        )
        memorial = self._run(props, fabrication="Soldado")
        self.assertIn("Anexo E — alma esbelta e FLT", memorial)
        self.assertIn("k_{pg}", memorial)
        self.assertIn("I_{yc}", memorial)
        self.assertIn(r"k_c=\max\left[0{,}35;\min", memorial)
        self.assertNotIn(r"k_{c,0}", memorial)
        self.assertNotIn(r"k_{c,sup}", memorial)
        self.assertIn("E.6.2", memorial)
        self.assertIn("E.6.3", memorial)
        chain_math = "".join(re.findall(r'class="formula-chain">\$\$(.*?)\$\$', memorial, re.S))
        self.assertNotIn(r"\quad;\quad", chain_math)

    def test_optional_branches_keep_one_to_one_equation_chains(self):
        memorial = self._run(
            use_stiffeners=True,
            stiffener_width=10.0, stiffener_thickness=1.0,
            stiffener_pair=True, stiffener_welded=True,
            has_tension_flange_holes=True, tension_flange_net_ratio=0.70,
            masonry_on_beam=True,
            support_relative_lateral_restrained=False,
            point_relative_lateral_restrained=False,
            local_unbraced_cm=300.0,
        )
        self.assertIn("Validação dos enrijecedores", memorial)
        self.assertIn("Sem ganho: alma em escoamento", memorial)
        self.assertIn(r"V_{Rd,0}=V_{Rd}(k_v=5{,}34)", memorial)
        self.assertIn(r"g_V=\frac{\Delta V_{Rd}}{V_{Rd,0}}\cdot100", memorial)
        self.assertIn("Furos na mesa tracionada", memorial)
        self.assertIn(r"\delta_{lim}=\min", memorial)
        self.assertEqual(memorial.count('class="formula-chain"'), memorial.count('class="calc-step"'))
        self.assertEqual(memorial.count('class="step-theory-panel"'), memorial.count('class="calc-step"'))
        chain_math = "".join(re.findall(r'class="formula-chain">\$\$(.*?)\$\$', memorial, re.S))
        self.assertNotIn(r"\quad;\quad", chain_math)
        for notation in (r"kN/m", r"\mathrm{N/A}", "FLA/mesa"):
            chain_math = chain_math.replace(notation, "")
        self.assertNotIn("/", chain_math)

    def test_numpy_integer_properties_render_as_numbers(self):
        props = dict(self.props)
        props["Iy"] = np.int64(600)
        props["Cw"] = np.int64(300_000)
        memorial = self._run(props)
        self.assertIn(r"\cdot600", memorial)
        self.assertIn(r"\frac{300000}{600}", memorial)
        self.assertNotIn(r"\cdotN/A", memorial)

    def test_adaptive_precision_removes_only_non_significant_trailing_zeroes(self):
        self.assertEqual(compact_number(500.0, 2), "500")
        self.assertEqual(compact_number(500.35, 2), "500.35")
        self.assertEqual(compact_number(2.5, 3), "2.5")
        self.assertEqual(compact_number(-0.0001, 3), "0")
        memorial = self._run(p_g_kn=0.0, p_q_kn=0.0)
        self.assertIn(r"500^4", memorial)
        self.assertIn(r"20000", memorial)
        self.assertNotIn(r"500.000", memorial)
        self.assertNotIn(r"20000.000", memorial)
        self.assertNotIn(r"0.000", memorial)

    def test_pure_udl_uses_closed_form_deflection_in_memorial(self):
        memorial = self._run(p_g_kn=0.0, p_q_kn=0.0)
        self.assertIn(
            r"\delta_{max}=\frac{5\cdot q_s\cdot L^4}{384\cdot E\cdot I_x}",
            memorial,
        )
        self.assertIn(r"x_\delta=\frac{L}{2}", memorial)
        self.assertNotIn(r"C_1\cdot x_\delta", memorial)
        self.assertNotIn(r"P_s\cdot\langle x_\delta-a\rangle", memorial)

    def test_local_web_sidesway_has_renderable_selected_cr_equation(self):
        memorial = self._run(
            support_relative_lateral_restrained=False,
            point_relative_lateral_restrained=False,
            loaded_flange_rotation_restrained=False,
            local_unbraced_cm=1000.0,
        )
        self.assertIn("Flambagem lateral da alma", memorial)
        self.assertRegex(memorial, r"C_r=(16|32)\\cdot E")
        self.assertNotIn(r"C_r=\begin{cases}", memorial)

    def test_engineering_diagrams_are_contextual_responsive_and_auditable(self):
        memorial = self._run(p_pos_cm=350.0, p_q_kn=11.5)
        for visual in (
            "beam-model", "shear-diagram", "moment-diagram",
            "cb-diagram", "deflection-diagram",
        ):
            self.assertIn(f'data-visual="{visual}"', memorial)
        self.assertEqual(memorial.count('data-visual="local-action"'), 3)
        self.assertGreaterEqual(memorial.count('class="engineering-svg"'), 8)
        self.assertEqual(
            memorial.count('class="engineering-svg"'),
            memorial.count('role="img"'),
        )
        self.assertIn('preserveAspectRatio="xMidYMid meet"', memorial)
        self.assertNotIn("<script", memorial)
        self.assertNotIn("<foreignObject", memorial)
        self.assertNotRegex(memorial, r"<svg[^>]+(?:onload|onclick|href=)")

        reaction_article = re.search(
            r'<article class="calc-step">(?:(?!</article>).)*<span class="calc-step-number">3\.3</span>(?:(?!</article>).)*</article>',
            memorial, re.S,
        ).group(0)
        effort_article = re.search(
            r'<article class="calc-step">(?:(?!</article>).)*<span class="calc-step-number">3\.4</span>(?:(?!</article>).)*</article>',
            memorial, re.S,
        ).group(0)
        cb_article = re.search(
            r'<article class="calc-step">(?:(?!</article>).)*<span class="calc-step-number">4\.1</span>(?:(?!</article>).)*</article>',
            memorial, re.S,
        ).group(0)
        deflection_article = re.search(
            r'<article class="calc-step">(?:(?!</article>).)*<span class="calc-step-number">8\.2</span>(?:(?!</article>).)*</article>',
            memorial, re.S,
        ).group(0)
        self.assertIn('data-visual="beam-model"', reaction_article)
        self.assertIn('data-visual="shear-diagram"', effort_article)
        self.assertIn('data-visual="moment-diagram"', effort_article)
        self.assertIn('data-visual="cb-diagram"', cb_article)
        self.assertIn('data-visual="deflection-diagram"', deflection_article)
        self.assertLess(reaction_article.index('formula-chain'), reaction_article.index('data-visual="beam-model"'))
        self.assertLess(deflection_article.index('formula-chain'), deflection_article.index('data-visual="deflection-diagram"'))
        self.assertIn("P em x = 3.5 m", deflection_article)
        self.assertRegex(deflection_article, r'data-critical-x-cm="\d+(?:\.\d+)?"')

    def test_engineering_diagrams_cover_all_supported_boundary_conditions(self):
        for support_type in (
            "Bi-apoiada",
            "Engastada e Livre (Balanço)",
            "Bi-engastada",
            "Engastada e Apoiada",
        ):
            with self.subTest(support_type=support_type):
                memorial = self._run(
                    support_type=support_type,
                    p_pos_cm=350.0,
                    p_q_kn=11.5,
                )
                self.assertIn('data-visual="beam-model"', memorial)
                self.assertIn('data-visual="shear-diagram"', memorial)
                self.assertIn('data-visual="moment-diagram"', memorial)
                self.assertIn('data-visual="deflection-diagram"', memorial)
                self.assertNotRegex(memorial.lower(), r'(?:nan|infinity)[^a-z]')
                self.assertNotIn('d=""', memorial)

    def test_diagram_critical_metadata_matches_the_analysis_response(self):
        response = analyze_beam(
            "simply_supported", 500.0,
            q=0.093521, point_load=11.5, point_position=350.0,
            E=20_000.0, I=3_437.0, samples=4_001,
        )
        efforts = effort_diagrams_visual(response)
        deflection = deflection_diagram_visual(response, 500.0 / 350.0)
        moment_figure = re.search(
            r'<figure class="engineering-visual" data-visual="moment-diagram".*?</figure>',
            efforts, re.S,
        ).group(0)
        self.assertIn(
            f'data-critical-x-cm="{compact_number(response.max_moment_position,3)}"',
            moment_figure,
        )
        self.assertIn(
            f'data-critical-value="{compact_number(response.moment_at(response.max_moment_position)/100,3)}"',
            moment_figure,
        )
        self.assertIn(
            f'data-critical-x-cm="{compact_number(response.max_deflection_position,3)}"',
            deflection,
        )
        self.assertIn(
            f'data-critical-value="{compact_number(response.max_deflection,4)}"',
            deflection,
        )
        for diagram in (moment_figure, deflection):
            self.assertEqual(diagram.count('data-endpoint="start"'), 1)
            self.assertEqual(diagram.count('data-endpoint="end"'), 1)

    def test_both_diagram_ends_are_labeled_without_duplicating_boundary_critical_label(self):
        response = analyze_beam(
            "fixed_fixed", 500.0,
            q=0.093521, point_load=0.0, point_position=250.0,
            E=20_000.0, I=3_437.0, samples=4_001,
        )
        efforts = effort_diagrams_visual(response)
        moment_figure = re.search(
            r'<figure class="engineering-visual" data-visual="moment-diagram".*?</figure>',
            efforts, re.S,
        ).group(0)
        endpoint_groups = re.findall(
            r'<g class="chart-endpoint" data-endpoint="(?:start|end)">.*?</g>',
            moment_figure, re.S,
        )

        self.assertEqual(len(endpoint_groups), 2)
        self.assertIn("x = 0 m", endpoint_groups[0])
        self.assertIn("x = 5 m", endpoint_groups[1])
        self.assertIn("Md =", endpoint_groups[0])
        self.assertIn("Md =", endpoint_groups[1])
        self.assertNotIn('<g class="chart-marker">', moment_figure)

    def test_sagging_moment_is_drawn_below_the_reference_axis(self):
        response = analyze_beam(
            "simply_supported", 500.0,
            q=0.093521, point_load=11.5, point_position=350.0,
            E=20_000.0, I=3_437.0, samples=4_001,
        )
        efforts = effort_diagrams_visual(response)
        moment_figure = re.search(
            r'<figure class="engineering-visual" data-visual="moment-diagram".*?</figure>',
            efforts, re.S,
        ).group(0)
        zero_y = float(re.search(r'<line[^>]*y1="([^"]+)"[^>]*class="chart-zero"', moment_figure).group(1))
        critical_y = float(re.search(r'<g class="chart-marker"><circle cx="[^"]+" cy="([^"]+)"', moment_figure).group(1))
        self.assertIn('data-positive-direction="down"', moment_figure)
        self.assertIn('+M abaixo', moment_figure)
        self.assertGreater(critical_y, zero_y)

    def test_cb_ordinates_and_unit_conversion_are_fully_auditable(self):
        memorial = self._run(p_pos_cm=350.0, p_q_kn=11.5)
        for expression in (
            r"x_A=x_0+\frac{L_b}{4}",
            r"M_A=|M(x_A)|",
            r"x_B=x_0+\frac{L_b}{2}",
            r"M_B=|M(x_B)|",
            r"x_C=x_0+\frac{3\cdot L_b}{4}",
            r"M_C=|M(x_C)|",
            r"x_{M,max}=\underset",
            r"\cdot R_m",
            r"M_{pl}\,[kN\!\cdot\!m]=\frac{Z_x\cdot f_y}{100}",
            r"M_{Rd,lim}\,[kN\!\cdot\!m]=\frac{1{,}50\cdot W_x\cdot f_y}{100\cdot\gamma_{a1}}",
        ):
            self.assertIn(expression, memorial)
        self.assertNotIn(r"C_b=\min(C_{b,calc};3{,}0)", memorial)


if __name__ == "__main__":
    unittest.main()
