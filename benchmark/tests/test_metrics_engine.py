import json
import tempfile
import unittest
from pathlib import Path

from benchmark.metrics.evaluator import (
    MetricsEngine,
    compute_confusion_matrix,
    compute_classification_metrics,
    compute_source_breakdown,
    compute_confidence_analysis,
    compute_latency_metrics,
)
from benchmark.scripts.compute_metrics import process_metrics


class TestMetricsEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)
        self.results_dir = self.temp_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_1_perfect_classification(self):
        results = [
            {"ground_truth": "ai", "predicted_label": "ai", "success": True},
            {"ground_truth": "ai", "predicted_label": "ai", "success": True},
            {"ground_truth": "human", "predicted_label": "human", "success": True},
            {"ground_truth": "human", "predicted_label": "human", "success": True},
        ]
        cm = compute_confusion_matrix(results)
        self.assertEqual(cm["tp"], 2)
        self.assertEqual(cm["fp"], 0)
        self.assertEqual(cm["tn"], 2)
        self.assertEqual(cm["fn"], 0)

        clf = compute_classification_metrics(cm)
        self.assertEqual(clf["accuracy"], 1.0)
        self.assertEqual(clf["precision"], 1.0)
        self.assertEqual(clf["recall"], 1.0)
        self.assertEqual(clf["specificity"], 1.0)
        self.assertEqual(clf["f1_score"], 1.0)
        self.assertEqual(clf["balanced_accuracy"], 1.0)

    def test_2_zero_accuracy_all_wrong(self):
        results = [
            {"ground_truth": "ai", "predicted_label": "human", "success": True},
            {"ground_truth": "human", "predicted_label": "ai", "success": True},
        ]
        cm = compute_confusion_matrix(results)
        self.assertEqual(cm["tp"], 0)
        self.assertEqual(cm["fp"], 1)
        self.assertEqual(cm["tn"], 0)
        self.assertEqual(cm["fn"], 1)

        clf = compute_classification_metrics(cm)
        self.assertEqual(clf["accuracy"], 0.0)
        self.assertEqual(clf["precision"], 0.0)
        self.assertEqual(clf["recall"], 0.0)
        self.assertEqual(clf["specificity"], 0.0)
        self.assertEqual(clf["f1_score"], 0.0)
        self.assertEqual(clf["balanced_accuracy"], 0.0)

    def test_3_mixed_predictions_confusion_matrix(self):
        # 2 TP, 1 FP, 3 TN, 1 FN (Total 7)
        results = [
            {"ground_truth": "ai", "predicted_label": "ai", "success": True},
            {"ground_truth": "ai", "predicted_label": "ai", "success": True},
            {"ground_truth": "human", "predicted_label": "ai", "success": True},
            {"ground_truth": "human", "predicted_label": "human", "success": True},
            {"ground_truth": "human", "predicted_label": "human", "success": True},
            {"ground_truth": "human", "predicted_label": "human", "success": True},
            {"ground_truth": "ai", "predicted_label": "human", "success": True},
        ]
        cm = compute_confusion_matrix(results)
        self.assertEqual(cm["tp"], 2)
        self.assertEqual(cm["fp"], 1)
        self.assertEqual(cm["tn"], 3)
        self.assertEqual(cm["fn"], 1)

        clf = compute_classification_metrics(cm)
        self.assertAlmostEqual(clf["accuracy"], 5 / 7, places=3)
        self.assertAlmostEqual(clf["precision"], 2 / 3, places=3)
        self.assertAlmostEqual(clf["recall"], 2 / 3, places=3)

    def test_4_empty_results_list(self):
        cm = compute_confusion_matrix([])
        clf = compute_classification_metrics(cm)
        perf = compute_latency_metrics([], total_duration_sec=1.0)

        self.assertEqual(cm["total_evaluated"], 0)
        self.assertEqual(clf["accuracy"], 0.0)
        self.assertEqual(perf["mean_ms"], 0.0)

    def test_5_handling_failed_runs(self):
        results = [
            {"ground_truth": "ai", "predicted_label": "ai", "success": True},
            {"ground_truth": "ai", "predicted_label": None, "success": False, "error": "Timeout"},
        ]
        cm = compute_confusion_matrix(results)
        self.assertEqual(cm["total_evaluated"], 1)
        self.assertEqual(cm["tp"], 1)

    def test_6_edge_case_zero_division(self):
        # 0 TP, 0 FP, 0 TN, 0 FN
        cm = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        clf = compute_classification_metrics(cm)
        self.assertEqual(clf["accuracy"], 0.0)
        self.assertEqual(clf["precision"], 0.0)
        self.assertEqual(clf["recall"], 0.0)
        self.assertEqual(clf["f1_score"], 0.0)

    def test_7_per_source_breakdown(self):
        results = [
            {"source": "phone_camera", "ground_truth": "human", "predicted_label": "human", "success": True},
            {"source": "phone_camera", "ground_truth": "human", "predicted_label": "ai", "success": True},
            {"source": "midjourney", "ground_truth": "ai", "predicted_label": "ai", "success": True},
        ]
        breakdown = compute_source_breakdown(results)
        self.assertIn("phone_camera", breakdown)
        self.assertIn("midjourney", breakdown)

        self.assertEqual(breakdown["phone_camera"]["total_images"], 2)
        self.assertEqual(breakdown["phone_camera"]["accuracy"], 0.5)
        self.assertEqual(breakdown["midjourney"]["accuracy"], 1.0)

    def test_8_latency_percentiles(self):
        results = [
            {"inference_time_ms": 100, "success": True},
            {"inference_time_ms": 200, "success": True},
            {"inference_time_ms": 300, "success": True},
            {"inference_time_ms": 400, "success": True},
            {"inference_time_ms": 500, "success": True},
        ]
        perf = compute_latency_metrics(results, total_duration_sec=2.0)
        self.assertEqual(perf["evaluated_count"], 5)
        self.assertEqual(perf["mean_ms"], 300.0)
        self.assertEqual(perf["min_ms"], 100)
        self.assertEqual(perf["max_ms"], 500)
        self.assertEqual(perf["p50_ms"], 300.0)
        self.assertEqual(perf["throughput_images_per_sec"], 2.5)

    def test_9_export_metrics_json(self):
        run_data = {
            "summary": {
                "run_id": "run_test_123",
                "timestamp": "2026-08-10T22:30:00Z",
                "model_key": "test_model",
                "model_name": "Test Model Detector",
                "total_selected": 2,
                "successful": 2,
                "failed": 0,
                "total_duration_sec": 1.0
            },
            "results": [
                {"ground_truth": "ai", "predicted_label": "ai", "inference_time_ms": 100, "success": True},
                {"ground_truth": "human", "predicted_label": "human", "inference_time_ms": 150, "success": True}
            ]
        }
        input_file = self.temp_dir / "latest_run.json"
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(run_data, f)

        metrics_out = process_metrics(input_path=input_file, output_dir=self.results_dir)

        latest_metrics = self.results_dir / "latest_metrics.json"
        run_metrics = self.results_dir / "metrics_run_test_123.json"

        self.assertTrue(latest_metrics.exists())
        self.assertTrue(run_metrics.exists())
        self.assertEqual(metrics_out["classification_metrics"]["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
