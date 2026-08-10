import json
import tempfile
import unittest
from pathlib import Path

from benchmark.reports.report_generator import ReportGenerator
from benchmark.scripts.generate_report import process_report_generation


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)
        self.reports_dir = self.temp_dir / "reports"
        self.results_dir = self.temp_dir / "results"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def create_sample_files(
        self,
        accuracy: float = 0.90,
        imbalanced: bool = False,
        missing_auc: bool = False,
        failed_cnt: int = 0,
        models_list: list = None
    ) -> tuple[Path, Path, Path]:
        run_file = self.results_dir / "latest_run.json"
        metrics_file = self.results_dir / "latest_metrics.json"
        analysis_file = self.results_dir / "latest_evaluation_analysis.json"

        run_data = {
            "summary": {
                "run_id": "run_test_789",
                "timestamp": "2026-08-10T22:54:00Z",
                "model_key": "hf_vit_deepfake",
                "model_name": "PyTorch ViT Classifier",
                "total_selected": 10,
                "successful": 10 - failed_cnt,
                "failed": failed_cnt,
                "total_duration_sec": 2.5
            },
            "results": [
                {
                    "id": f"img_{i}",
                    "filename": f"test_{i}.jpg",
                    "ground_truth": "human" if i < 5 else "ai",
                    "predicted_label": "human" if i < 5 else "ai",
                    "ai_probability": 10.0 if i < 5 else 90.0,
                    "confidence": "High",
                    "source": "phone_camera" if i < 5 else "midjourney",
                    "success": True,
                    "inference_time_ms": 250
                } for i in range(10)
            ]
        }

        metrics_data = {
            "metadata": run_data["summary"],
            "confusion_matrix": {"tp": 5, "fp": 0, "tn": 5, "fn": 0, "total_evaluated": 10},
            "classification_metrics": {
                "accuracy": accuracy,
                "precision": 1.0,
                "recall": 1.0,
                "specificity": 1.0,
                "f1_score": accuracy,
                "balanced_accuracy": accuracy
            },
            "per_source_breakdown": {
                "phone_camera": {"sample_count": 5, "accuracy": 1.0},
                "midjourney": {"sample_count": 5, "accuracy": 1.0}
            },
            "latency_and_performance": {
                "evaluated_count": 10,
                "mean_ms": 250.0,
                "min_ms": 200,
                "max_ms": 300,
                "p50_ms": 250.0
            }
        }

        auc_val = None if missing_auc else 0.98
        mod_list = models_list or [
            {
                "model_key": "hf_vit_deepfake",
                "model_name": "PyTorch ViT Classifier",
                "sample_count": 10,
                "accuracy": accuracy,
                "precision": 1.0,
                "recall": 1.0,
                "f1_score": accuracy,
                "roc_auc": auc_val,
                "false_positive_rate": 0.0,
                "false_negative_rate": 0.0,
                "avg_inference_time_ms": 250.0,
                "failure_rate": 0.0
            }
        ]

        analysis_data = {
            "summary_metadata": run_data["summary"],
            "confusion_matrix": {
                "raw": {"true_negative": 5, "false_positive": 0, "false_negative": 0, "true_positive": 5},
                "normalized": {
                    "human_actual": {"predicted_human": 1.0, "predicted_ai": 0.0},
                    "ai_actual": {"predicted_human": 0.0, "predicted_ai": 1.0}
                }
            },
            "error_analysis": {"false_positive_rate": 0.0, "false_negative_rate": 0.0, "false_positives": [], "false_negatives": []},
            "dataset_balance": {
                "human_count": 1 if imbalanced else 5,
                "ai_count": 9 if imbalanced else 5,
                "human_percentage": 10.0 if imbalanced else 50.0,
                "ai_percentage": 90.0 if imbalanced else 50.0,
                "is_balanced": not imbalanced,
                "warning": "Dataset is strongly imbalanced." if imbalanced else None
            },
            "source_level_analysis": {
                "phone_camera": {"sample_count": 5, "has_sufficient_samples": True, "accuracy": 1.0},
                "midjourney": {"sample_count": 5, "has_sufficient_samples": True, "accuracy": 1.0}
            },
            "model_level_analysis": {"models": mod_list},
            "error_categories": {"high_confidence_errors": {"count": 0}},
            "analysis_summary": {
                "overall_assessment": "High performance.",
                "strengths": ["High accuracy."],
                "weaknesses": [],
                "warnings": ["Dataset is strongly imbalanced."] if imbalanced else [],
                "recommendations": ["Investigate false negatives."]
            }
        }

        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(run_data, f)
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f)
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f)

        return run_file, metrics_file, analysis_file

    def test_1_complete_benchmark_data(self):
        r, m, a = self.create_sample_files()
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        rep = generator.generate_report_dict()

        self.assertEqual(rep["executive_summary"]["dataset_size"], 10)
        self.assertEqual(rep["metrics"]["accuracy"], 0.90)

    def test_2_missing_metrics_file(self):
        r, m, a = self.create_sample_files()
        m.unlink()

        with self.assertRaises(FileNotFoundError) as ctx:
            process_report_generation(run_path=r, metrics_path=m, analysis_path=a, output_dir=self.reports_dir)
        self.assertIn("Metrics File", str(ctx.exception))

    def test_3_missing_analysis_file(self):
        r, m, a = self.create_sample_files()
        a.unlink()

        with self.assertRaises(FileNotFoundError) as ctx:
            process_report_generation(run_path=r, metrics_path=m, analysis_path=a, output_dir=self.reports_dir)
        self.assertIn("Analysis File", str(ctx.exception))

    def test_4_empty_dataset(self):
        generator = ReportGenerator(run_data={}, metrics_data={}, analysis_data={})
        rep = generator.generate_report_dict()
        self.assertEqual(rep["executive_summary"]["dataset_size"], 0)

    def test_5_single_model_benchmark(self):
        r, m, a = self.create_sample_files()
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        reports = generator.generate_all_reports(self.reports_dir)

        self.assertTrue(reports["json"].exists())
        self.assertTrue(reports["csv"].exists())
        self.assertTrue(reports["markdown"].exists())
        self.assertTrue(reports["pdf"].exists())

    def test_6_multi_model_benchmark(self):
        multi_models = [
            {"model_name": "Model 1", "sample_count": 10, "accuracy": 0.95, "f1_score": 0.95},
            {"model_name": "Model 2", "sample_count": 10, "accuracy": 0.85, "f1_score": 0.84}
        ]
        r, m, a = self.create_sample_files(models_list=multi_models)
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        csv_p = generator.generate_csv_report(self.reports_dir, "multi_test")

        with open(csv_p, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 3)  # Header + 2 model rows

    def test_7_missing_roc_auc(self):
        r, m, a = self.create_sample_files(missing_auc=True)
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        rep = generator.generate_report_dict()
        self.assertIsNone(rep["metrics"]["roc_auc"])

    def test_8_imbalanced_dataset(self):
        r, m, a = self.create_sample_files(imbalanced=True)
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        rep = generator.generate_report_dict()
        self.assertIn("Dataset is strongly imbalanced.", rep["warnings"])

    def test_9_failed_predictions(self):
        r, m, a = self.create_sample_files(failed_cnt=2)
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        rep = generator.generate_report_dict()
        self.assertEqual(rep["executive_summary"]["failed_analyses"], 2)

    def test_10_pdf_generation(self):
        r, m, a = self.create_sample_files()
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        pdf_p = generator.generate_pdf_report(self.reports_dir, "test_pdf")
        self.assertTrue(pdf_p.exists())
        self.assertGreater(pdf_p.stat().st_size, 1000)

    def test_11_csv_generation(self):
        r, m, a = self.create_sample_files()
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        csv_p = generator.generate_csv_report(self.reports_dir, "test_csv")
        self.assertTrue(csv_p.exists())

        with open(csv_p, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("model,samples,accuracy", content)

    def test_12_json_generation(self):
        r, m, a = self.create_sample_files()
        generator = ReportGenerator.load_from_files(run_file=r, metrics_file=m, analysis_file=a)
        json_p = generator.generate_json_report(self.reports_dir, "test_json")
        self.assertTrue(json_p.exists())

        with open(json_p, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("report_metadata", data)
        self.assertIn("executive_summary", data)
        self.assertIn("confusion_matrix", data)


if __name__ == "__main__":
    unittest.main()
