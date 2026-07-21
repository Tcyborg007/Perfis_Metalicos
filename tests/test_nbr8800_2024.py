import math
import unittest

from calculos_nbr8800_2024 import (
    analyze_beam,
    calculate_cb,
    combine_els,
    deflection_limit,
    flexural_strength_i,
    overall_status,
    shear_strength_i,
    validate_material,
)


class BeamAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.L = 500.0
        self.q = 0.10
        self.E = 20_000.0
        self.I = 10_000.0

    def test_simply_supported_udl(self):
        result = analyze_beam("Bi-apoiada", self.L, self.q, E=self.E, I=self.I)
        self.assertAlmostEqual(result.max_moment, self.q * self.L**2 / 8.0, places=8)
        self.assertAlmostEqual(result.max_shear, self.q * self.L / 2.0, places=8)
        expected_delta = 5.0 * self.q * self.L**4 / (384.0 * self.E * self.I)
        self.assertAlmostEqual(result.max_deflection, expected_delta, places=8)

    def test_simply_supported_eccentric_point_load(self):
        P, a = 30.0, 175.0
        b = self.L - a
        result = analyze_beam("Bi-apoiada", self.L, point_load=P, point_position=a)
        self.assertAlmostEqual(result.reaction_left, P * b / self.L, places=8)
        self.assertAlmostEqual(result.reaction_right, P * a / self.L, places=8)
        self.assertAlmostEqual(result.max_moment, P * a * b / self.L, places=8)

    def test_cantilever_udl(self):
        result = analyze_beam(
            "Engastada e Livre (Balanço)", self.L, self.q, E=self.E, I=self.I
        )
        self.assertAlmostEqual(result.max_moment, self.q * self.L**2 / 2.0, places=8)
        expected_delta = self.q * self.L**4 / (8.0 * self.E * self.I)
        self.assertAlmostEqual(result.max_deflection, expected_delta, places=8)

    def test_cantilever_eccentric_point_load(self):
        P, a = 30.0, 175.0
        result = analyze_beam(
            "Engastada e Livre (Balanço)", self.L,
            point_load=P, point_position=a, E=self.E, I=self.I,
        )
        self.assertAlmostEqual(result.max_moment, P * a, places=8)
        expected_free_end = P * a**2 * (3.0 * self.L - a) / (6.0 * self.E * self.I)
        self.assertAlmostEqual(result.max_deflection, expected_free_end, places=8)

    def test_fixed_fixed_udl(self):
        result = analyze_beam("Bi-engastada", self.L, self.q, E=self.E, I=self.I)
        self.assertAlmostEqual(result.moment_left, -self.q * self.L**2 / 12.0, places=8)
        self.assertAlmostEqual(result.moment_right, -self.q * self.L**2 / 12.0, places=8)
        expected_delta = self.q * self.L**4 / (384.0 * self.E * self.I)
        self.assertAlmostEqual(result.max_deflection, expected_delta, places=6)

    def test_fixed_fixed_central_point_load(self):
        P = 30.0
        result = analyze_beam(
            "Bi-engastada", self.L, point_load=P, point_position=self.L / 2.0,
            E=self.E, I=self.I,
        )
        self.assertAlmostEqual(result.reaction_left, P / 2.0, places=8)
        self.assertAlmostEqual(result.moment_left, -P * self.L / 8.0, places=8)
        self.assertAlmostEqual(result.max_deflection, P * self.L**3 / (192.0 * self.E * self.I), places=6)

    def test_propped_cantilever_udl(self):
        result = analyze_beam("Engastada e Apoiada", self.L, self.q)
        self.assertAlmostEqual(result.reaction_left, 5.0 * self.q * self.L / 8.0, places=8)
        self.assertAlmostEqual(result.reaction_right, 3.0 * self.q * self.L / 8.0, places=8)
        self.assertAlmostEqual(result.moment_left, -self.q * self.L**2 / 8.0, places=8)
        self.assertAlmostEqual(result.moment_right, 0.0, places=8)

    def test_propped_cantilever_eccentric_point_load_compatibility(self):
        P, a = 30.0, 175.0
        result = analyze_beam(
            "Engastada e Apoiada", self.L, point_load=P, point_position=a,
            E=self.E, I=self.I,
        )
        expected_rb = P * a**2 * (3.0 * self.L - a) / (2.0 * self.L**3)
        self.assertAlmostEqual(result.reaction_right, expected_rb, places=8)
        self.assertAlmostEqual(result.moment_right, 0.0, places=8)
        self.assertAlmostEqual(result.deflections[-1], 0.0, places=10)

    def test_cb_for_simply_supported_udl(self):
        result = analyze_beam("Bi-apoiada", self.L, self.q)
        cb = calculate_cb(result)
        self.assertAlmostEqual(cb["Cb"], 1.1363636363636365, places=8)
        self.assertAlmostEqual(cb["xMmax"], self.L / 2.0, places=10)

    def test_cb_mmax_is_analytic_and_independent_of_deflection_mesh(self):
        coarse = analyze_beam(
            "Bi-apoiada", self.L, q=0.093521,
            point_load=11.5, point_position=350.0, samples=101,
        )
        fine = analyze_beam(
            "Bi-apoiada", self.L, q=0.093521,
            point_load=11.5, point_position=350.0, samples=4001,
        )
        coarse_cb = calculate_cb(coarse)
        fine_cb = calculate_cb(fine)
        self.assertAlmostEqual(coarse_cb["xMmax"], fine_cb["xMmax"], places=10)
        self.assertAlmostEqual(coarse_cb["Mmax"], fine_cb["Mmax"], places=10)
        self.assertAlmostEqual(coarse_cb["Cb"], fine_cb["Cb"], places=10)

    def test_cantilever_deflection_reference_length_is_double(self):
        self.assertEqual(
            deflection_limit("Engastada e Livre (Balanço)", 500.0, 250.0), 4.0
        )


class ResistanceTests(unittest.TestCase):
    def setUp(self):
        self.props = {
            "d": 50.0,
            "bf": 20.0,
            "tw": 0.8,
            "tf": 1.2,
            "h_faces": 47.6,
            "h_clear": 45.0,
            "Wx": 1_000.0,
            "Zx": 1_150.0,
            "Iy": 600.0,
            "J": 20.0,
            "Cw": 300_000.0,
            "ry": 2.5,
        }

    def test_material_limits(self):
        self.assertEqual(validate_material(34.5, 45.0), [])
        self.assertTrue(validate_material(46.0, 55.0))
        self.assertTrue(validate_material(34.5, 38.0))

    def test_flexural_strength_respects_global_elastic_cap(self):
        result = flexural_strength_i(
            self.props, fy=34.5, fu=45.0, E=20_000.0, Lb=5.0, Cb=1.0,
            fabrication="Laminado"
        )
        self.assertLessEqual(result["Mrd"], 1.5 * self.props["Wx"] * 34.5 / 1.10 + 1e-9)
        self.assertGreater(result["Mrd"], 0.0)

    def test_unstiffened_web_uses_kv_5_34(self):
        result = shear_strength_i(self.props, fy=34.5, E=20_000.0)
        self.assertEqual(result["kv"], 5.34)

    def test_errata_stiffener_j_expression(self):
        h = self.props["h_clear"]
        result = shear_strength_i(
            self.props,
            fy=34.5,
            E=20_000.0,
            stiffener_spacing=0.5 * h,
            stiffener_width=10.0,
            stiffener_thickness=1.0,
            stiffener_pair=True,
            stiffener_welded_to_web_and_flanges=True,
        )
        self.assertAlmostEqual(result["j"], 8.0, places=8)
        self.assertIn("Errata", result["reference"])

    def test_stiffener_inertia_uses_web_midplane_axis(self):
        b, t, tw = 10.0, 1.0, self.props["tw"]
        result = shear_strength_i(
            self.props, fy=34.5, E=20_000.0,
            stiffener_spacing=0.5 * self.props["h_clear"],
            stiffener_width=b, stiffener_thickness=t, stiffener_pair=True,
            stiffener_welded_to_web_and_flanges=True,
        )
        one_plate = t * b**3 / 12.0 + t * b * ((tw + b) / 2.0) ** 2
        self.assertAlmostEqual(result["I_st"], 2.0 * one_plate, places=8)

    def test_tension_flange_holes_can_govern(self):
        result = flexural_strength_i(
            self.props, fy=34.5, fu=45.0, E=20_000.0, Lb=5.0, Cb=1.0,
            fabrication="Laminado",
            gross_tension_flange_area=24.0,
            net_tension_flange_area=8.0,
        )
        self.assertFalse(result["rupture_condition_ok"])
        self.assertTrue(result["holes_checked"])
        self.assertEqual(result["Afg_tension"], 24.0)
        self.assertEqual(result["Afn_tension"], 8.0)
        self.assertIsNotNone(result["Mrd_rupture"])
        self.assertLessEqual(result["Mrd"], result["Mrd_rupture"])

    def test_annex_e_slender_welded_web_is_calculated(self):
        props = dict(self.props)
        props.update(
            d=124.0,
            bf=30.0,
            tw=0.6,
            tf=2.0,
            h_faces=120.0,
            h_clear=120.0,
            Wx=3_000.0,
            Zx=3_400.0,
            Iy=4_500.0,
            J=50.0,
            Cw=2_000_000.0,
            ry=3.0,
        )
        result = flexural_strength_i(
            props, fy=34.5, fu=45.0, E=20_000.0, Lb=300.0, Cb=1.0,
            fabrication="Soldado"
        )
        self.assertTrue(result["slender_web"])
        self.assertEqual(result["applicability_issues"], [])
        self.assertGreater(result["Mrd"], 0.0)
        self.assertIsNotNone(result["kpg"])


class CombinationAndStatusTests(unittest.TestCase):
    def test_els_combination_references_exact_normative_items(self):
        expected_items = {
            "rare": "4.8.7.3.4",
            "frequent": "4.8.7.3.3",
            "quasi_permanent": "4.8.7.3.2",
            "variable_only": "4.8.7.3.1",
        }
        for combination, item in expected_items.items():
            with self.subTest(combination=combination):
                result = combine_els(0.01, 0.02, 0.001, combination=combination)
                self.assertIn(item, result["reference"])
                self.assertIn("B.2.4", result["reference"])
                self.assertIn("B.3.3", result["reference"])

    def test_els_rejects_invalid_psi(self):
        with self.assertRaises(ValueError):
            combine_els(0.01, 0.02, 0.001, psi1=1.1)

    def test_proven_failure_has_priority_over_pending_scope(self):
        self.assertEqual(
            overall_status(["NÃO VERIFICADO", "REPROVADO", "APROVADO"]),
            "REPROVADO",
        )


if __name__ == "__main__":
    unittest.main()
