import json
import tempfile
import unittest
from pathlib import Path

from benchmark.metrics.comparison_engine import ModelComparisonEngine
from benchmark.scripts.compare_models import process_model_comparison


class TestModelComparisonEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)
        self.results_dir = self.temp_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.engine = ModelComparisonEngine(min_source_samples=3)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def create_mock_run(self, model_key: str, model_name: str, raw_items: list) -> dict:
        total_selected = len(raw_items)
        successful = sum(1 for r in raw_items if r.get("success", True))
        failed = total_selected - successful
        return {
            "summary": {
                "run_id": f"run_{model_key}",
                "timestamp": "2026-08-10T22:56:00Z",
                "model_key": model_key,
                "model_name": model_name,
                "total_selected": total_selected,
                "successful": successful,
                "failed": failed,
                "total_duration_sec": 1.0
            },
            "results": raw_items
        }

    def test_1_two_successful_models(self):
        m1_items = [
            {"id": "1", "filename": "1.jpg", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "source": "phone_camera", "success": True, "inference_time_ms": 100},
            {"id": "2", "filename": "2.jpg", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "source": "midjourney", "success": True, "inference_time_ms": 110}
        ]
        m2_items = [
            {"id": "1", "filename": "1.jpg", "ground_truth": "human", "predicted_label": "human", "ai_probability": 15.0, "source": "phone_camera", "success": True, "inference_time_ms": 50},
            {"id": "2", "filename": "2.jpg", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 85.0, "source": "midjourney", "success": True, "inference_time_ms": 60}
        ]

        run1 = self.create_mock_run("model_a", "Model A", m1_items)
        run2 = self.create_mock_run("model_b", "Model B", m2_items)

        res = self.engine.compare_model_runs([run1, run2])

        self.assertEqual(len(res["models"]), 2)
        self.assertIn("model_a", res["models"])
        self.assertIn("model_b", res["models"])
        self.assertEqual(res["agreement"]["overall_agreement_rate"], 1.0)
        self.assertEqual(res["agreement"]["disagreement_count"], 0)

    def test_2_three_successful_models(self):
        items_template = lambda pred: [
            {"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "ai", "predicted_label": pred, "ai_probability": 80.0 if pred=="ai" else 20.0, "source": "midjourney", "success": True, "inference_time_ms": 100}
            for i in range(5)
        ]

        run1 = self.create_mock_run("m1", "Model 1", items_template("ai"))
        run2 = self.create_mock_run("m2", "Model 2", items_template("ai"))
        run3 = self.create_mock_run("m3", "Model 3", items_template("ai"))

        res = self.engine.compare_model_runs([run1, run2, run3])

        self.assertEqual(len(res["models"]), 3)
        self.assertEqual(res["comparison_metadata"]["models_count"], 3)
        self.assertEqual(res["comparison_metadata"]["ranking_status"], "ranked")

    def test_3_one_unavailable_model(self):
        m1_items = [
            {"id": "1", "filename": "1.jpg", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True, "inference_time_ms": 100}
        ]
        m2_failed = [
            {"id": "1", "filename": "1.jpg", "ground_truth": "human", "predicted_label": None, "success": False, "error": "PyTorch weights missing", "error_type": "FileNotFoundError", "inference_time_ms": 0}
        ]

        run1 = self.create_mock_run("m1", "Model 1", m1_items)
        run2 = self.create_mock_run("m2_failed", "Failed Model 2", m2_failed)

        res = self.engine.compare_model_runs([run1, run2])

        self.assertTrue(res["models"]["m1"]["available"])
        self.assertFalse(res["models"]["m2_failed"]["available"])
        self.assertIn("PyTorch weights missing", res["models"]["m2_failed"]["unavailable_reason"])

    def test_4_model_failure(self):
        m_items = [
            {"id": "1", "ground_truth": "human", "predicted_label": "human", "success": True, "inference_time_ms": 100},
            {"id": "2", "ground_truth": "ai", "predicted_label": None, "success": False, "error": "OOM", "inference_time_ms": 0}
        ]
        run1 = self.create_mock_run("m1", "Model 1", m_items)
        res = self.engine.compare_model_runs([run1])

        self.assertEqual(res["models"]["m1"]["failure_rate"], 0.5)

    def test_5_different_prediction_results(self):
        m1_items = [{"id": "1", "filename": "1.jpg", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "confidence": "High", "success": True}]
        m2_items = [{"id": "1", "filename": "1.jpg", "ground_truth": "ai", "predicted_label": "human", "ai_probability": 30.0, "confidence": "Low", "success": True}]

        run1 = self.create_mock_run("m1", "Model 1", m1_items)
        run2 = self.create_mock_run("m2", "Model 2", m2_items)

        res = self.engine.compare_model_runs([run1, run2])

        self.assertEqual(res["agreement"]["disagreement_count"], 1)
        self.assertEqual(len(res["disagreements"]), 1)
        dis = res["disagreements"][0]
        self.assertEqual(dis["id"], "1")
        self.assertEqual(dis["model_predictions"]["m1"]["predicted_label"], "ai")
        self.assertEqual(dis["model_predictions"]["m2"]["predicted_label"], "human")

    def test_6_complete_model_agreement(self):
        m1_items = [{"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True} for i in range(3)]
        m2_items = [{"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 85.0, "success": True} for i in range(3)]

        run1 = self.create_mock_run("m1", "Model 1", m1_items)
        run2 = self.create_mock_run("m2", "Model 2", m2_items)

        res = self.engine.compare_model_runs([run1, run2])

        self.assertEqual(res["agreement"]["overall_agreement_rate"], 1.0)
        self.assertEqual(res["agreement"]["disagreement_count"], 0)

    def test_7_complete_model_disagreement(self):
        m1_items = [{"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True} for i in range(3)]
        m2_items = [{"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "ai", "predicted_label": "human", "ai_probability": 20.0, "success": True} for i in range(3)]

        run1 = self.create_mock_run("m1", "Model 1", m1_items)
        run2 = self.create_mock_run("m2", "Model 2", m2_items)

        res = self.engine.compare_model_runs([run1, run2])

        self.assertEqual(res["agreement"]["overall_agreement_rate"], 0.0)
        self.assertEqual(res["agreement"]["disagreement_count"], 3)

    def test_8_missing_roc_auc(self):
        # Single class (all AI), ROC-AUC cannot be calculated
        m1_items = [{"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True} for i in range(5)]
        run1 = self.create_mock_run("m1", "Model 1", m1_items)

        res = self.engine.compare_model_runs([run1])
        self.assertIsNone(res["models"]["m1"]["metrics"]["roc_auc"])

    def test_9_multiple_sources(self):
        m1_items = [
            {"id": "1", "filename": "1.jpg", "source": "phone_camera", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True},
            {"id": "2", "filename": "2.jpg", "source": "midjourney", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True}
        ]
        run1 = self.create_mock_run("m1", "Model 1", m1_items)

        res = self.engine.compare_model_runs([run1])
        srcs = res["source_comparison"]
        self.assertIn("phone_camera", srcs)
        self.assertIn("midjourney", srcs)

    def test_10_insufficient_source_samples(self):
        m1_items = [
            {"id": "1", "filename": "1.jpg", "source": "dslr", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True}
        ]
        run1 = self.create_mock_run("m1", "Model 1", m1_items)

        res = self.engine.compare_model_runs([run1])
        dslr_info = res["source_comparison"]["dslr"]["m1"]
        self.assertFalse(dslr_info["has_sufficient_samples"])

    def test_11_ranking_with_sufficient_data(self):
        m1_items = [{"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "human" if i<3 else "ai", "predicted_label": "human" if i<3 else "ai", "ai_probability": 10.0 if i<3 else 90.0, "success": True, "inference_time_ms": 100} for i in range(6)]
        m2_items = [{"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "human" if i<3 else "ai", "predicted_label": "ai", "ai_probability": 80.0, "success": True, "inference_time_ms": 500} for i in range(6)]

        run1 = self.create_mock_run("m1", "Model Superior", m1_items)
        run2 = self.create_mock_run("m2", "Model Flawed", m2_items)

        res = self.engine.compare_model_runs([run1, run2])

        self.assertEqual(res["comparison_metadata"]["ranking_status"], "ranked")
        ranking = res["ranking"]
        self.assertEqual(len(ranking), 2)
        self.assertEqual(ranking[0]["model_key"], "m1")  # Model Superior should rank #1

    def test_12_ranking_with_insufficient_data(self):
        m1_items = [{"id": f"{i}", "filename": f"{i}.jpg", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True} for i in range(2)]
        run1 = self.create_mock_run("m1", "Model 1", m1_items)

        res = self.engine.compare_model_runs([run1])

        self.assertEqual(res["comparison_metadata"]["ranking_status"], "insufficient_data")
        self.assertEqual(res["ranking"], "insufficient_data")
        self.assertIn("Insufficient data", res["warnings"][0])


if __name__ == "__main__":
    unittest.main()
