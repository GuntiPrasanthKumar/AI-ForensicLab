import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from benchmark.scripts.runner import BenchmarkRunner


class TestBenchmarkRunner(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)
        self.datasets_dir = self.temp_dir / "datasets"
        self.results_dir = self.temp_dir / "results"
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.results_dir / "dataset_index.json"

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def create_dummy_image(self, rel_path: str, width: int = 100, height: int = 100, color: str = "blue") -> Path:
        full_path = self.datasets_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (width, height), color=color)
        img.save(full_path)
        return full_path

    def write_dataset_index(self, images_list: list) -> Path:
        data = {
            "summary": {
                "total_images": len(images_list),
                "valid_images": sum(1 for img in images_list if img.get("valid", True))
            },
            "images": images_list
        }
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return self.index_path

    def test_1_empty_dataset(self):
        self.write_dataset_index([])
        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir)
        runs = runner.run()

        self.assertEqual(len(runs), 1)
        summary = runs[0]["summary"]
        self.assertEqual(summary["total_selected"], 0)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(len(runs[0]["results"]), 0)

    @patch("benchmark.scripts.runner.analyze_image_authenticity")
    def test_2_one_valid_image(self, mock_analyze):
        img_path = self.create_dummy_image("human/phone_camera/test1.jpg")
        img_rec = {
            "id": "img_00001",
            "path": f"datasets/human/phone_camera/test1.jpg",
            "filename": "test1.jpg",
            "label": "human",
            "source": "phone_camera",
            "extension": "jpg",
            "valid": True,
            "duplicate": False
        }
        self.write_dataset_index([img_rec])

        mock_analyze.return_value = {
            "aiProbability": 12.0,
            "humanProbability": 88.0,
            "confidence": "High",
            "risk_level": "Low Risk",
            "provider_used": "PyTorch ViT Detector"
        }

        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir)
        runs = runner.run()

        summary = runs[0]["summary"]
        self.assertEqual(summary["total_selected"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

        res = runs[0]["results"][0]
        self.assertTrue(res["success"])
        self.assertEqual(res["ground_truth"], "human")
        self.assertEqual(res["predicted_label"], "human")
        self.assertEqual(res["ai_probability"], 12.0)
        self.assertEqual(res["model_name"], "PyTorch ViT Detector")
        self.assertGreaterEqual(res["inference_time_ms"], 0)

    @patch("benchmark.scripts.runner.analyze_image_authenticity")
    def test_3_multiple_valid_images(self, mock_analyze):
        self.create_dummy_image("human/phone_camera/test1.jpg")
        self.create_dummy_image("ai/midjourney/render1.png")

        images_list = [
            {
                "id": "img_00001",
                "path": "datasets/human/phone_camera/test1.jpg",
                "filename": "test1.jpg",
                "label": "human",
                "source": "phone_camera",
                "valid": True,
                "duplicate": False
            },
            {
                "id": "img_00002",
                "path": "datasets/ai/midjourney/render1.png",
                "filename": "render1.png",
                "label": "ai",
                "source": "midjourney",
                "valid": True,
                "duplicate": False
            }
        ]
        self.write_dataset_index(images_list)

        mock_analyze.return_value = {
            "aiProbability": 85.0,
            "humanProbability": 15.0,
            "confidence": "High",
            "risk_level": "High Risk",
            "provider_used": "Test Engine"
        }

        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir)
        runs = runner.run()

        summary = runs[0]["summary"]
        self.assertEqual(summary["total_selected"], 2)
        self.assertEqual(summary["successful"], 2)

    def test_4_missing_image(self):
        img_rec = {
            "id": "img_00001",
            "path": "datasets/human/phone_camera/nonexistent.jpg",
            "filename": "nonexistent.jpg",
            "label": "human",
            "source": "phone_camera",
            "valid": True,
            "duplicate": False
        }
        self.write_dataset_index([img_rec])

        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir)
        runs = runner.run()

        summary = runs[0]["summary"]
        self.assertEqual(summary["total_selected"], 1)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 1)

        res = runs[0]["results"][0]
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "FileNotFoundError")

    def test_5_invalid_image(self):
        img_rec = {
            "id": "img_00001",
            "path": "datasets/human/phone_camera/corrupt.jpg",
            "filename": "corrupt.jpg",
            "label": "human",
            "source": "phone_camera",
            "valid": False,
            "duplicate": False
        }
        self.write_dataset_index([img_rec])

        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir, include_invalid=False)
        runs = runner.run()

        summary = runs[0]["summary"]
        self.assertEqual(summary["total_selected"], 0)
        self.assertEqual(summary["skipped"], 1)

    @patch("benchmark.scripts.runner.analyze_image_authenticity")
    def test_6_model_failure(self, mock_analyze):
        self.create_dummy_image("ai/midjourney/render1.png")
        img_rec = {
            "id": "img_00001",
            "path": "datasets/ai/midjourney/render1.png",
            "filename": "render1.png",
            "label": "ai",
            "source": "midjourney",
            "valid": True,
            "duplicate": False
        }
        self.write_dataset_index([img_rec])

        mock_analyze.side_effect = RuntimeError("GPU Out of Memory")

        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir)
        runs = runner.run()

        summary = runs[0]["summary"]
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 1)

        res = runs[0]["results"][0]
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "RuntimeError")
        self.assertIn("GPU Out of Memory", res["error"])

    @patch("benchmark.scripts.runner.analyze_image_authenticity")
    def test_7_partial_benchmark_failure(self, mock_analyze):
        self.create_dummy_image("human/phone_camera/test1.jpg")
        self.create_dummy_image("ai/midjourney/render1.png")

        images_list = [
            {
                "id": "img_00001",
                "path": "datasets/human/phone_camera/test1.jpg",
                "filename": "test1.jpg",
                "label": "human",
                "source": "phone_camera",
                "valid": True,
                "duplicate": False
            },
            {
                "id": "img_00002",
                "path": "datasets/ai/midjourney/render1.png",
                "filename": "render1.png",
                "label": "ai",
                "source": "midjourney",
                "valid": True,
                "duplicate": False
            }
        ]
        self.write_dataset_index(images_list)

        # First image succeeds, second image fails
        mock_analyze.side_effect = [
            {"aiProbability": 10.0, "humanProbability": 90.0, "provider_used": "Model 1"},
            ValueError("Model processing timeout")
        ]

        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir)
        runs = runner.run()

        summary = runs[0]["summary"]
        self.assertEqual(summary["total_selected"], 2)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 1)

    @patch("benchmark.scripts.runner.analyze_image_authenticity")
    def test_8_model_selection(self, mock_analyze):
        self.create_dummy_image("human/phone_camera/test1.jpg")
        img_rec = {
            "id": "img_00001",
            "path": "datasets/human/phone_camera/test1.jpg",
            "filename": "test1.jpg",
            "label": "human",
            "source": "phone_camera",
            "valid": True,
            "duplicate": False
        }
        self.write_dataset_index([img_rec])

        mock_analyze.return_value = {"aiProbability": 20.0, "humanProbability": 80.0, "provider_used": "Test Engine"}

        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir, model="hf_vit_deepfake")
        runs = runner.run()

        self.assertEqual(runs[0]["summary"]["model_key"], "hf_vit_deepfake")

    @patch("benchmark.scripts.runner.analyze_image_authenticity")
    def test_9_result_file_generation(self, mock_analyze):
        self.create_dummy_image("human/phone_camera/test1.jpg")
        img_rec = {
            "id": "img_00001",
            "path": "datasets/human/phone_camera/test1.jpg",
            "filename": "test1.jpg",
            "label": "human",
            "source": "phone_camera",
            "valid": True,
            "duplicate": False
        }
        self.write_dataset_index([img_rec])

        mock_analyze.return_value = {"aiProbability": 15.0, "humanProbability": 85.0, "provider_used": "Test Engine"}

        runner = BenchmarkRunner(index_path=self.index_path, output_dir=self.results_dir)
        runner.run()

        latest_run = self.results_dir / "latest_run.json"
        self.assertTrue(latest_run.exists())

        benchmark_runs = list(self.results_dir.glob("benchmark_run_*.json"))
        self.assertGreaterEqual(len(benchmark_runs), 1)


if __name__ == "__main__":
    unittest.main()
