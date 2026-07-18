import unittest
import re
import numpy as np

from main import perform_all_checks


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
            0.05, (10.0, 250.0), "Bi-apoiada", input_mode,
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
        self.assertNotIn(r"\begin{aligned}", memorial)
        self.assertEqual(memorial.count('class="formula-chain"'), memorial.count('class="calc-step"'))
        self.assertGreater(memorial.count('class="equation-pair"'), memorial.count('class="calc-step"'))
        self.assertGreaterEqual(memorial.count('class="equation-line '), 2 * memorial.count('class="equation-pair"'))
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
        self.assertNotIn(r"\Rightarrow", memorial)
        self.assertNotIn("S" + "NR", memorial.upper())
        chain_math = "".join(re.findall(r'class="equation-line[^"]*">\$\$(.*?)\$\$', memorial, re.S))
        self.assertNotIn(r"\quad;\quad", chain_math)
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
        self.assertIn(r"k_{c,0}=\frac{4}", memorial)
        self.assertIn(r"k_{c,sup}=\min", memorial)
        self.assertIn(r"k_c=\max", memorial)
        self.assertNotIn(r"k_c=\max\left[", memorial)
        chain_math = "".join(re.findall(r'class="equation-line[^"]*">\$\$(.*?)\$\$', memorial, re.S))
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
        self.assertIn("Furos na mesa tracionada", memorial)
        self.assertIn(r"\delta_{lim}=\min", memorial)
        self.assertEqual(memorial.count('class="formula-chain"'), memorial.count('class="calc-step"'))
        self.assertEqual(memorial.count('class="step-theory-panel"'), memorial.count('class="calc-step"'))
        chain_math = "".join(re.findall(r'class="equation-line[^"]*">\$\$(.*?)\$\$', memorial, re.S))
        self.assertNotIn(r"\quad;\quad", chain_math)
        for notation in (r"kN/m", r"\mathrm{N/A}", "FLA/mesa"):
            chain_math = chain_math.replace(notation, "")
        self.assertNotIn("/", chain_math)

    def test_numpy_integer_properties_render_as_numbers(self):
        props = dict(self.props)
        props["Iy"] = np.int64(600)
        props["Cw"] = np.int64(300_000)
        memorial = self._run(props)
        self.assertIn(r"\cdot600.000", memorial)
        self.assertIn(r"\frac{300000.000}{600.000}", memorial)
        self.assertNotIn(r"\cdotN/A", memorial)


if __name__ == "__main__":
    unittest.main()
