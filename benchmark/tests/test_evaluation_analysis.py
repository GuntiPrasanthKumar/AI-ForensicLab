import json
import tempfile
import unittest
from pathlib import Path

from benchmark.metrics.evaluator import MetricsEngine
from benchmark.metrics.analysis_engine import EvaluationAnalysisEngine, compute_roc_auc
from benchmark.scripts.evaluate_results import process_evaluation_analysis


class TestEvaluationAnalysisEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)
        self.results_dir = self.temp_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.engine = EvaluationAnalysisEngine(min_source_samples=3)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def create_mock_run(self, raw_items: list, model_name: str = "Test Model") -> dict:
        total_selected = len(raw_items)
        successful = sum(1 for item in raw_items if item.get("success", True))
        failed = total_selected - successful
        return {
            "summary": {
                "run_id": "mock_run_001",
                "timestamp": "2026-08-10T22:50:00Z",
                "model_key": "test_model",
                "model_name": model_name,
                "total_selected": total_selected,
                "successful": successful,
                "failed": failed,
                "total_duration_sec": 1.5
            },
            "results": raw_items
        }

    def run_analysis_from_items(self, raw_items: list, min_samples: int = 3) -> dict:
        run_data = self.create_mock_run(raw_items)
        metrics_data = MetricsEngine.compute_all_metrics(run_data)
        engine = EvaluationAnalysisEngine(min_source_samples=min_samples)
        return engine.analyze(metrics_data, run_data)

    def test_1_perfect_classifier(self):
        items = [
            {"id": "1", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "confidence": "High", "source": "phone_camera", "success": True, "inference_time_ms": 100},
            {"id": "2", "ground_truth": "human", "predicted_label": "human", "ai_probability": 15.0, "confidence": "High", "source": "phone_camera", "success": True, "inference_time_ms": 110},
            {"id": "3", "ground_truth": "human", "predicted_label": "human", "ai_probability": 5.0, "confidence": "High", "source": "phone_camera", "success": True, "inference_time_ms": 90},
            {"id": "4", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "confidence": "High", "source": "midjourney", "success": True, "inference_time_ms": 120},
            {"id": "5", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 95.0, "confidence": "High", "source": "midjourney", "success": True, "inference_time_ms": 130},
            {"id": "6", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 88.0, "confidence": "High", "source": "midjourney", "success": True, "inference_time_ms": 115},
        ]
        res = self.run_analysis_from_items(items)

        raw_cm = res["confusion_matrix"]["raw"]
        norm_cm = res["confusion_matrix"]["normalized"]

        self.assertEqual(raw_cm["true_negative"], 3)
        self.assertEqual(raw_cm["false_positive"], 0)
        self.assertEqual(raw_cm["false_negative"], 0)
        self.assertEqual(raw_cm["true_positive"], 3)

        self.assertEqual(norm_cm["human_actual"]["predicted_human"], 1.0)
        self.assertEqual(norm_cm["human_actual"]["predicted_ai"], 0.0)
        self.assertEqual(norm_cm["ai_actual"]["predicted_human"], 0.0)
        self.assertEqual(norm_cm["ai_actual"]["predicted_ai"], 1.0)

        self.assertEqual(res["error_analysis"]["false_positive_rate"], 0.0)
        self.assertEqual(res["error_analysis"]["false_negative_rate"], 0.0)

    def test_2_mixed_classifier(self):
        items = [
            {"id": "1", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True},
            {"id": "2", "ground_truth": "human", "predicted_label": "human", "ai_probability": 15.0, "success": True},
            {"id": "3", "ground_truth": "human", "predicted_label": "ai", "ai_probability": 70.0, "success": True},  # FP
            {"id": "4", "ground_truth": "ai", "predicted_label": "human", "ai_probability": 30.0, "success": True},  # FN
            {"id": "5", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 85.0, "success": True},
        ]
        res = self.run_analysis_from_items(items)

        err = res["error_analysis"]
        self.assertAlmostEqual(err["false_positive_rate"], 1 / 3, places=3)
        self.assertAlmostEqual(err["false_negative_rate"], 1 / 2, places=3)

        self.assertEqual(len(err["false_positives"]), 1)
        self.assertEqual(len(err["false_negatives"]), 1)

    def test_3_all_human_dataset(self):
        items = [
            {"id": str(i), "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True}
            for i in range(5)
        ]
        res = self.run_analysis_from_items(items)

        bal = res["dataset_balance"]
        self.assertEqual(bal["human_count"], 5)
        self.assertEqual(bal["ai_count"], 0)
        self.assertEqual(bal["human_percentage"], 100.0)
        self.assertEqual(bal["ai_percentage"], 0.0)

        # Ensure no NaN or ZeroDivisionError in normalized matrix
        norm_cm = res["confusion_matrix"]["normalized"]
        self.assertEqual(norm_cm["ai_actual"]["predicted_human"], 0.0)
        self.assertEqual(norm_cm["ai_actual"]["predicted_ai"], 0.0)

    def test_4_all_ai_dataset(self):
        items = [
            {"id": str(i), "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True}
            for i in range(5)
        ]
        res = self.run_analysis_from_items(items)

        bal = res["dataset_balance"]
        self.assertEqual(bal["human_count"], 0)
        self.assertEqual(bal["ai_count"], 5)
        self.assertEqual(bal["ai_percentage"], 100.0)

        norm_cm = res["confusion_matrix"]["normalized"]
        self.assertEqual(norm_cm["human_actual"]["predicted_human"], 0.0)
        self.assertEqual(norm_cm["human_actual"]["predicted_ai"], 0.0)

    def test_5_balanced_dataset(self):
        items = [
            {"id": f"h_{i}", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True} for i in range(5)
        ] + [
            {"id": f"a_{i}", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True} for i in range(5)
        ]
        res = self.run_analysis_from_items(items)

        bal = res["dataset_balance"]
        self.assertTrue(bal["is_balanced"])
        self.assertEqual(bal["balance_status"], "Balanced")
        self.assertIsNone(bal["warning"])

    def test_6_imbalanced_dataset(self):
        items = [
            {"id": f"h_{i}", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True} for i in range(9)
        ] + [
            {"id": "a_1", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True}
        ]
        res = self.run_analysis_from_items(items)

        bal = res["dataset_balance"]
        self.assertFalse(bal["is_balanced"])
        self.assertEqual(bal["balance_status"], "Imbalanced")
        self.assertIn("dataset is imbalanced", bal["warning"])
        self.assertIn("Accuracy may not represent real-world performance", res["analysis_summary"]["recommendations"][0])

    def test_7_false_positive_heavy_dataset(self):
        items = [
            {"id": f"h_{i}", "ground_truth": "human", "predicted_label": "ai", "ai_probability": 80.0, "success": True} for i in range(4)
        ] + [
            {"id": "h_correct", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True}
        ]
        res = self.run_analysis_from_items(items)

        err = res["error_analysis"]
        self.assertEqual(err["false_positive_rate"], 0.8)
        recs = res["analysis_summary"]["recommendations"]
        self.assertTrue(any("Human images are frequently classified as AI" in r for r in recs))

    def test_8_false_negative_heavy_dataset(self):
        items = [
            {"id": f"a_{i}", "ground_truth": "ai", "predicted_label": "human", "ai_probability": 20.0, "success": True} for i in range(4)
        ] + [
            {"id": "a_correct", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True}
        ]
        res = self.run_analysis_from_items(items)

        err = res["error_analysis"]
        self.assertEqual(err["false_negative_rate"], 0.8)
        recs = res["analysis_summary"]["recommendations"]
        self.assertTrue(any("AI-generated images are frequently missed" in r for r in recs))

    def test_9_multiple_models(self):
        scores = [0.1, 0.2, 0.8, 0.9]
        targets = [0, 0, 1, 1]
        auc = compute_roc_auc(targets, scores)
        self.assertEqual(auc, 1.0)

        items = [
            {"id": "1", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True},
            {"id": "2", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True}
        ]
        res = self.run_analysis_from_items(items)
        models = res["model_level_analysis"]["models"]
        self.assertEqual(len(models), 1)
        self.assertIsNotNone(models[0]["roc_auc"])

    def test_10_multiple_sources(self):
        items = [
            {"id": f"p_{i}", "source": "phone_camera", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True} for i in range(3)
        ] + [
            {"id": f"m_{i}", "source": "midjourney", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True} for i in range(3)
        ]
        res = self.run_analysis_from_items(items, min_samples=3)

        srcs = res["source_level_analysis"]
        self.assertIn("phone_camera", srcs)
        self.assertIn("midjourney", srcs)

        self.assertTrue(srcs["phone_camera"]["has_sufficient_samples"])
        self.assertTrue(srcs["midjourney"]["has_sufficient_samples"])

    def test_11_insufficient_source_sample_size(self):
        items = [
            {"id": "1", "source": "dslr", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True}
        ]
        res = self.run_analysis_from_items(items, min_samples=5)

        srcs = res["source_level_analysis"]
        self.assertIn("dslr", srcs)
        self.assertFalse(srcs["dslr"]["has_sufficient_samples"])
        self.assertIn("Insufficient sample size", srcs["dslr"]["insufficient_sample_warning"])

    def test_12_high_confidence_incorrect_predictions(self):
        items = [
            # High confidence error: Ground truth AI, predicted Human with low AI prob (10.0%) and confidence High
            {"id": "1", "ground_truth": "ai", "predicted_label": "human", "ai_probability": 10.0, "confidence": "High", "success": True}
        ]
        res = self.run_analysis_from_items(items)

        conf = res["confidence_analysis"]
        self.assertGreater(conf["error_confidence_breakdown"]["high_confidence_errors"], 0)
        self.assertTrue(any("high model confidence" in w for w in res["analysis_summary"]["warnings"]))

    def test_13_low_confidence_incorrect_predictions(self):
        items = [
            # Low confidence error: Ground truth AI, predicted Human with AI prob 45.0% and confidence Low
            {"id": "1", "ground_truth": "ai", "predicted_label": "human", "ai_probability": 45.0, "confidence": "Low", "success": True}
        ]
        res = self.run_analysis_from_items(items)

        conf = res["confidence_analysis"]
        self.assertGreater(conf["error_confidence_breakdown"]["low_confidence_errors"], 0)
        self.assertGreater(conf["error_confidence_breakdown"]["threshold_boundary_errors"], 0)
        self.assertTrue(any("decision boundary" in w for w in res["analysis_summary"]["warnings"]))

    def test_14_process_evaluation_analysis_export(self):
        run_data = self.create_mock_run([
            {"id": "1", "ground_truth": "human", "predicted_label": "human", "ai_probability": 10.0, "success": True},
            {"id": "2", "ground_truth": "ai", "predicted_label": "ai", "ai_probability": 90.0, "success": True}
        ])
        metrics_data = MetricsEngine.compute_all_metrics(run_data)

        metrics_file = self.temp_dir / "latest_metrics.json"
        raw_file = self.temp_dir / "latest_run.json"

        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f)
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(run_data, f)

        res = process_evaluation_analysis(
            input_metrics_path=metrics_file,
            raw_run_path=raw_file,
            output_dir=self.results_dir
        )

        latest_analysis = self.results_dir / "latest_evaluation_analysis.json"
        self.assertTrue(latest_analysis.exists())
        self.assertEqual(res["confusion_matrix"]["raw"]["true_positive"], 1)


if __name__ == "__main__":
    unittest.main()
