"""
Unit Tests for Dataset Manager
"""
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from benchmark.scripts.dataset_manager import DatasetManager
from benchmark.scripts.scanner import DatasetScanner
from benchmark.scripts.validator import ImageValidator
from benchmark.scripts.deduplicator import ImageDeduplicator


class TestDatasetManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)
        self.output_index = self.temp_dir / "results" / "dataset_index.json"

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def create_dummy_image(self, rel_path: str, width: int = 100, height: int = 100, color: str = "red") -> Path:
        full_path = self.temp_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (width, height), color=color)
        img.save(full_path)
        return full_path

    def create_dummy_file(self, rel_path: str, content: bytes) -> Path:
        full_path = self.temp_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(content)
        return full_path

    def test_empty_dataset_directory(self):
        manager = DatasetManager(dataset_dir=self.temp_dir, output_index_path=self.output_index)
        index_data = manager.process()

        summary = index_data["summary"]
        self.assertEqual(summary["total_images"], 0)
        self.assertEqual(summary["valid_images"], 0)
        self.assertEqual(summary["invalid_images"], 0)
        self.assertEqual(len(index_data["images"]), 0)
        self.assertTrue(self.output_index.exists())

    def test_valid_human_image(self):
        self.create_dummy_image("human/phone_camera/photo1.jpg", 800, 600, "blue")
        manager = DatasetManager(dataset_dir=self.temp_dir, output_index_path=self.output_index)
        index_data = manager.process()

        summary = index_data["summary"]
        self.assertEqual(summary["total_images"], 1)
        self.assertEqual(summary["valid_images"], 1)
        self.assertEqual(summary["human_images"], 1)
        self.assertEqual(summary["ai_images"], 0)

        img_rec = index_data["images"][0]
        self.assertEqual(img_rec["label"], "human")
        self.assertEqual(img_rec["source"], "phone_camera")
        self.assertEqual(img_rec["extension"], "jpg")
        self.assertEqual(img_rec["width"], 800)
        self.assertEqual(img_rec["height"], 600)
        self.assertTrue(img_rec["valid"])
        self.assertIsNone(img_rec["invalid_reason"])
        self.assertFalse(img_rec["duplicate"])

    def test_valid_ai_image(self):
        self.create_dummy_image("ai/midjourney/render1.png", 1024, 1024, "green")
        manager = DatasetManager(dataset_dir=self.temp_dir, output_index_path=self.output_index)
        index_data = manager.process()

        summary = index_data["summary"]
        self.assertEqual(summary["total_images"], 1)
        self.assertEqual(summary["valid_images"], 1)
        self.assertEqual(summary["ai_images"], 1)

        img_rec = index_data["images"][0]
        self.assertEqual(img_rec["label"], "ai")
        self.assertEqual(img_rec["source"], "midjourney")
        self.assertEqual(img_rec["extension"], "png")
        self.assertTrue(img_rec["valid"])

    def test_unsupported_file(self):
        self.create_dummy_file("human/dslr/notes.txt", b"This is a text document.")
        self.create_dummy_image("human/dslr/valid_dslr.jpg", 500, 500)

        manager = DatasetManager(dataset_dir=self.temp_dir, output_index_path=self.output_index)
        index_data = manager.process()

        summary = index_data["summary"]
        # Unsupported .txt file should be ignored during scanning
        self.assertEqual(summary["total_images"], 1)
        self.assertEqual(summary["valid_images"], 1)

    def test_corrupted_image(self):
        self.create_dummy_file("human/screenshots/corrupt.jpg", b"INVALID_HEADER_NOT_AN_IMAGE_DATA_123456789")

        manager = DatasetManager(dataset_dir=self.temp_dir, output_index_path=self.output_index)
        index_data = manager.process()

        summary = index_data["summary"]
        self.assertEqual(summary["total_images"], 1)
        self.assertEqual(summary["valid_images"], 0)
        self.assertEqual(summary["invalid_images"], 1)

        img_rec = index_data["images"][0]
        self.assertFalse(img_rec["valid"])
        self.assertIsNotNone(img_rec["invalid_reason"])
        self.assertIn("Corrupted", img_rec["invalid_reason"])

    def test_empty_file(self):
        self.create_dummy_file("ai/flux/zero_bytes.webp", b"")

        manager = DatasetManager(dataset_dir=self.temp_dir, output_index_path=self.output_index)
        index_data = manager.process()

        summary = index_data["summary"]
        self.assertEqual(summary["total_images"], 1)
        self.assertEqual(summary["valid_images"], 0)
        self.assertEqual(summary["invalid_images"], 1)

        img_rec = index_data["images"][0]
        self.assertFalse(img_rec["valid"])
        self.assertEqual(img_rec["invalid_reason"], "Zero-byte file")

    def test_duplicate_image(self):
        # Create image file
        img_path1 = self.create_dummy_image("human/phone_camera/photo1.jpg", 400, 400, "purple")
        
        # Copy exact content to another directory with different filename
        with open(img_path1, "rb") as f:
            content = f.read()
        self.create_dummy_file("human/edited/photo1_edited.jpg", content)

        manager = DatasetManager(dataset_dir=self.temp_dir, output_index_path=self.output_index)
        index_data = manager.process()

        summary = index_data["summary"]
        self.assertEqual(summary["total_images"], 2)
        self.assertEqual(summary["valid_images"], 2)
        self.assertEqual(summary["duplicate_images"], 1)

        duplicates = [img["duplicate"] for img in index_data["images"]]
        self.assertEqual(duplicates.count(True), 1)
        self.assertEqual(duplicates.count(False), 1)

    def test_nested_directories(self):
        self.create_dummy_image("ai/stable_diffusion/sub1/sub2/nested_sd.jpg", 600, 600)

        manager = DatasetManager(dataset_dir=self.temp_dir, output_index_path=self.output_index)
        index_data = manager.process()

        summary = index_data["summary"]
        self.assertEqual(summary["total_images"], 1)
        self.assertEqual(summary["valid_images"], 1)

        img_rec = index_data["images"][0]
        self.assertEqual(img_rec["label"], "ai")
        self.assertEqual(img_rec["source"], "stable_diffusion")


if __name__ == "__main__":
    unittest.main()
