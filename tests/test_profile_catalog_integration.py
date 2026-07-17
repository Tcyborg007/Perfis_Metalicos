import math
from pathlib import Path
import unittest

import pandas as pd

from calculos_nbr8800_2024 import (
    flexural_strength_i,
    local_compression_strength,
    shear_strength_i,
)


ROOT = Path(__file__).resolve().parents[1]


def profile_properties(row):
    area_column = next(name for name in row.index if name.endswith("(cm2)"))
    return {
        "d": row["d (mm)"] / 10.0,
        "bf": row["bf (mm)"] / 10.0,
        "tw": row["tw (mm)"] / 10.0,
        "tf": row["tf (mm)"] / 10.0,
        "h_faces": row["h (mm)"] / 10.0,
        "h_clear": row["d' (mm)"] / 10.0,
        "Area": row[area_column],
        "Ix": row["Ix (cm4)"],
        "Wx": row["Wx (cm3)"],
        "Zx": row["Zx (cm3)"],
        "Iy": row["Iy (cm4)"],
        "ry": row["ry (cm)"],
        "J": row["It (cm4)"],
        "Cw": row["Cw (cm6)"],
        "Peso": row["Massa Linear (kg/m)"],
    }


class ProfileCatalogIntegrationTests(unittest.TestCase):
    def test_every_catalog_profile_has_a_deterministic_result(self):
        workbook = pd.read_excel(ROOT / "perfis.xlsx", sheet_name=None)
        checked = 0
        for sheet, frame in workbook.items():
            fabrication = "Laminado" if sheet == "Laminados" else "Soldado"
            for _, row in frame.iterrows():
                props = profile_properties(row)
                flexure = flexural_strength_i(
                    props, fy=34.5, fu=45.0, E=20_000.0,
                    Lb=500.0, Cb=1.0, fabrication=fabrication,
                )
                shear = shear_strength_i(props, fy=34.5, E=20_000.0)
                local = local_compression_strength(
                    props, fy=34.5, E=20_000.0, bearing_length=10.0,
                    distance_to_end=0.0, fabrication=fabrication,
                    relative_lateral_movement_restrained=True,
                )

                for value in (shear["Vrd"], local["FRd"]):
                    self.assertTrue(math.isfinite(value) and value > 0.0)
                if flexure["applicability_issues"]:
                    self.assertEqual(flexure["Mrd"], 0.0)
                else:
                    self.assertTrue(math.isfinite(flexure["Mrd"]))
                    self.assertGreater(flexure["Mrd"], 0.0)
                checked += 1

        self.assertGreater(checked, 100)


if __name__ == "__main__":
    unittest.main()
