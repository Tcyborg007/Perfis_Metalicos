import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StreamlitLayoutTests(unittest.TestCase):
    def test_wide_page_config_runs_on_every_main_execution(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        main_function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        first_statement = main_function.body[0]
        self.assertIsInstance(first_statement, ast.Expr)
        call = first_statement.value
        self.assertIsInstance(call, ast.Call)
        self.assertIsInstance(call.func, ast.Attribute)
        self.assertEqual(call.func.attr, "set_page_config")
        keywords = {item.arg: item.value for item in call.keywords}
        self.assertEqual(ast.literal_eval(keywords["layout"]), "wide")

        top_level_page_config = [
            node for node in tree.body
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "set_page_config"
        ]
        self.assertEqual(top_level_page_config, [])

    def test_layout_css_uses_stable_streamlit_container_selector(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn('[data-testid="stMainBlockContainer"]', source)
        self.assertIn("max-width: 1600px !important", source)
        self.assertIn("width: 100% !important", source)

    def test_header_has_no_external_navigation_or_centered_logo(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertNotIn("create_navigation_buttons", source)
        self.assertNotIn("nav-button-secondary", source)
        self.assertNotIn("Logo HQ Engenharia", source)
        self.assertNotIn("lh3.googleusercontent.com", source)

    def test_memorial_diagrams_have_responsive_and_print_styles(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn(".container .engineering-visual", source)
        self.assertIn(".container .engineering-svg", source)
        self.assertIn("width: 100%; height: auto", source)
        self.assertIn(".container .visual-metrics", source)
        self.assertIn('[data-visual="deflection-diagram"] .svg-critical-label', source)
        self.assertIn(".container .visual-svg-wrap { background: white !important; }", source)


if __name__ == "__main__":
    unittest.main()
