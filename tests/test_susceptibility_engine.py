"""
tests/test_susceptibility_engine.py
Comprehensive Unit Test Suite for the Physics-Informed AHP GLOF Susceptibility Engine.

NASA Space Apps Challenge 2026 - Dancing with the SARs.
GLACIAL FORENSICS Project - Stage 2A.
"""

import os
import unittest
import numpy as np

os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_LOG_MODE"] = "PYTHON"

from glof_watch.susceptibility import (
    GLOFSusceptibilityEngine,
    DEFAULT_PAIRWISE_MATRIX,
    CRITERIA_KEYS,
    CRITERIA_NAMES,
    QUALIFYING_FIVE_SITES_FEATURES,
    get_site_susceptibility,
    run_oat_sensitivity_analysis
)


class TestGLOFSusceptibilityEngine(unittest.TestCase):
    """Unit tests for the AHP mathematical engine and site evaluation logic."""

    @classmethod
    def setUpClass(cls):
        from glof_watch.ui.app import GLOFWatchApp
        cls.app = GLOFWatchApp()
        cls.root = cls.app.build()

    def setUp(self):
        self.engine = GLOFSusceptibilityEngine()

    def test_01_matrix_reciprocal_and_shape(self):
        """Verifies that the pairwise comparison matrix is 8x8 and strictly reciprocal."""
        mat = DEFAULT_PAIRWISE_MATRIX
        self.assertEqual(mat.shape, (8, 8))
        self.assertTrue(np.allclose(mat, 1.0 / mat.T), "Matrix must be strictly reciprocal A[j,i] = 1/A[i,j]")
        self.assertTrue(np.allclose(np.diag(mat), 1.0), "Diagonal elements must all equal 1.0")

    def test_02_ahp_consistency_ratio(self):
        """Verifies that the Consistency Ratio (CR) is well below Saaty's 0.10 threshold."""
        self.assertGreaterEqual(self.engine.lambda_max, 8.0, "Lambda max must be >= n (8.0)")
        self.assertAlmostEqual(self.engine.lambda_max, 8.3110, places=3)
        self.assertAlmostEqual(self.engine.ci, 0.0444, places=3)
        self.assertAlmostEqual(self.engine.cr, 0.0315, places=3)
        self.assertLess(self.engine.cr, 0.10, "Consistency Ratio must satisfy CR < 0.10")

    def test_03_normalized_weights(self):
        """Verifies that normalized priority weights sum to 1.0 and respect geotechnical hierarchy."""
        weights = self.engine.weights
        self.assertEqual(len(weights), 8)
        self.assertAlmostEqual(float(np.sum(weights)), 1.0, places=5)
        self.assertTrue(all(w > 0 for w in weights), "All weights must be strictly positive")

        w_dict = self.engine.get_criteria_weights()
        # Dam Type must be highest weighted criterion (~28.5%)
        self.assertAlmostEqual(w_dict["dam_type"], 0.2850, places=3)
        # Freeboard Deficit must be second highest (~20.4%)
        self.assertAlmostEqual(w_dict["freeboard_deficit"], 0.2041, places=3)
        # Glacier Proximity must be third (~15.3%)
        self.assertAlmostEqual(w_dict["glacier_proximity"], 0.1530, places=3)

    def test_04_qualifying_five_lakes_evaluation(self):
        """Verifies scores and relative ranking of the five qualifying benchmark lakes."""
        scores = {}
        for site_id, feat in QUALIFYING_FIVE_SITES_FEATURES.items():
            res = self.engine.evaluate_lake(feat)
            self.assertFalse(res["is_excluded"])
            self.assertIsNotNone(res["susceptibility_score"])
            self.assertEqual(res["data_completeness_pct"], 100.0)
            self.assertIn(res["susceptibility_category"], ["VERY HIGH", "HIGH", "MODERATE", "REGULATED"])
            scores[site_id] = res["susceptibility_score"]

        # Exact expected physics scores
        self.assertAlmostEqual(scores["kyagar"], 77.09, places=1)
        self.assertAlmostEqual(scores["rumbak"], 74.54, places=1)
        self.assertAlmostEqual(scores["gya"], 66.81, places=1)
        self.assertAlmostEqual(scores["parkachik"], 56.08, places=1)
        self.assertAlmostEqual(scores["drang_drung"], 51.93, places=1)

        # Verify ranking order: Kyagar > Rumbak > Gya > Parkachik > Drang-Drung
        ranking = sorted(scores.keys(), key=lambda s: scores[s], reverse=True)
        self.assertEqual(ranking, ["kyagar", "rumbak", "gya", "parkachik", "drang_drung"])

    def test_05_phyang_cirque_explicit_exclusion(self):
        """Verifies that Phyang Cirque is disqualified and excluded from GLOF calculations."""
        res = get_site_susceptibility("phyang")
        self.assertTrue(res["is_excluded"])
        self.assertIsNone(res["susceptibility_score"])
        self.assertEqual(res["susceptibility_category"], "EXCLUDED")
        self.assertIn("DISQUALIFIED", res["explanation"])
        self.assertIn("cloudburst", res["explanation"].lower())

        # Also test via 'cirque' key
        res_cirque = get_site_susceptibility("cirque")
        self.assertTrue(res_cirque["is_excluded"])
        self.assertEqual(res_cirque["susceptibility_category"], "EXCLUDED")

    def test_06_dynamic_missing_data_renormalization(self):
        """Verifies that missing indicators are handled via weight re-normalization without data fabrication."""
        # Simulated lake with missing freeboard and missing area
        test_lake = {
            "Site_ID": "test_lake",
            "Site_Name": "Test Incomplete Lake",
            "Dam_Geomorphic_Type": "Ice-Cored Lateral Moraine",
            "Dam_Freeboard_m": "missing",  # Missing
            "Glacier_Snout_Proximity_m": 0.0,
            "Mean_Catchment_Slope_deg": 28.0,
            "Baseline_Lake_Area_ha": "missing",  # Missing
            "Relative_Area_Change_pct": 50.0,
            "Downstream_Hydraulic_Gradient_m_per_m": 0.15,
            "Delta_VV_Backscatter_dB": 5.0
        }

        res = self.engine.evaluate_lake(test_lake)
        self.assertFalse(res["is_excluded"])
        self.assertIsNotNone(res["susceptibility_score"])

        # Data completeness must reflect missing weights (Freeboard ~20.4% + Area ~8.3% missing -> ~71.3% complete)
        self.assertLess(res["data_completeness_pct"], 100.0)
        self.assertAlmostEqual(res["data_completeness_pct"], 71.3, delta=1.0)

        # Active weights must sum to 1.0 across available indicators
        active_weights = res["active_weights"]
        self.assertEqual(active_weights["freeboard_deficit"], 0.0)
        self.assertEqual(active_weights["lake_area"], 0.0)
        sum_active = sum(active_weights.values())
        self.assertAlmostEqual(sum_active, 1.0, places=3)

        # Missing indicators list must explicitly contain the missing names
        self.assertIn("Dam Freeboard Deficit & Buffer", res["missing_indicators"])
        self.assertIn("Lake Surface Area & Water Storage", res["missing_indicators"])

    def test_07_oat_sensitivity_analysis_robustness(self):
        """Verifies that One-At-A-Time weight perturbations yield >= 90% ranking stability."""
        sens = run_oat_sensitivity_analysis(perturbations=[-0.20, -0.10, +0.10, +0.20])
        self.assertEqual(sens["total_perturbation_tests"], 32)
        # Exactly 1 inversion out of 32 (96.9% stability)
        self.assertLessEqual(sens["rank_inversions_count"], 2)
        self.assertGreaterEqual(sens["overall_ranking_robustness_pct"], 90.0)
        self.assertEqual(sens["base_ranking"], ["kyagar", "rumbak", "gya", "parkachik", "drang_drung"])

    def test_08_inventory_ahp_integration(self):
        """Verifies that glof_watch.ui.inventory correctly stores AHP scores and categories."""
        from glof_watch.ui.inventory import HIMALAYAN_GLACIAL_LAKE_INVENTORY, get_lake_by_id

        kyagar = get_lake_by_id("kyagar")
        self.assertIsNotNone(kyagar)
        self.assertEqual(kyagar.get("ahp_category"), "HIGH")
        self.assertAlmostEqual(kyagar.get("ahp_score"), 77.09, places=1)

        rumbak = get_lake_by_id("rumbak")
        self.assertIsNotNone(rumbak)
        self.assertEqual(rumbak.get("ahp_category"), "HIGH")
        self.assertAlmostEqual(rumbak.get("ahp_score"), 74.54, places=1)

        drang_drung = get_lake_by_id("drang_drung")
        self.assertIsNotNone(drang_drung)
        self.assertEqual(drang_drung.get("ahp_category"), "MODERATE")

        phyang = get_lake_by_id("phyang")
        self.assertIsNotNone(phyang)
        self.assertTrue(phyang.get("is_excluded"))
        self.assertEqual(phyang.get("ahp_category"), "EXCLUDED")
        self.assertFalse(phyang.get("historical_glof"))

    def test_09_ui_analysis_screen_ahp_hub_instantiation(self):
        """Verifies that AnalysisScreen instantiates with the AHP Susceptibility view mode and card hub."""
        screen = self.app.analysis_screen
        self.assertTrue(hasattr(screen, "btn_view_ahp"), "AnalysisScreen must possess btn_view_ahp")
        self.assertTrue(hasattr(screen, "card_ahp_hub"), "AnalysisScreen must possess card_ahp_hub")
        self.assertTrue(hasattr(screen, "_update_ahp_telemetry_card"), "AnalysisScreen must have _update_ahp_telemetry_card")

        # Test switching view to AHP
        screen.switch_view_mode("ahp")
        self.assertEqual(screen.active_view_mode, "ahp")
        self.assertIn(screen.card_ahp_hub, screen.view_container.children)


if __name__ == "__main__":
    unittest.main()
