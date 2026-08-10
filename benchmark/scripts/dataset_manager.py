import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from benchmark.scripts.scanner import DatasetScanner
from benchmark.scripts.validator import ImageValidator
from benchmark.scripts.deduplicator import ImageDeduplicator
from benchmark.scripts.stats import DatasetStatisticsCalculator

logging.basicConfig(
    level=logging.INFO,
    format="[DatasetManager] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DatasetManager")


class DatasetManager:
    """
    Main Dataset Manager coordinating dataset scanning, image validation,
    metadata extraction, content deduplication, statistical aggregation,
    and structured JSON index generation.
    """

    def __init__(self, dataset_dir: str | Path = None, output_index_path: str | Path = None):
        project_root = Path(__file__).resolve().parent.parent.parent
        self.dataset_dir = Path(dataset_dir).resolve() if dataset_dir else (project_root / "benchmark" / "datasets")
        self.output_index_path = Path(output_index_path).resolve() if output_index_path else (project_root / "benchmark" / "results" / "dataset_index.json")

    def build_index(self) -> Dict[str, Any]:
        """
        Scans, validates, deduplicates, and computes statistics for the dataset.
        Returns a structured index dictionary.
        """
        logger.info(f"Scanning dataset directory: {self.dataset_dir}")
        scanner = DatasetScanner(self.dataset_dir)
        scanned_files = scanner.scan()

        logger.info(f"Found {len(scanned_files)} candidate image files.")

        raw_records: List[Dict[str, Any]] = []
        for idx, file_item in enumerate(scanned_files, start=1):
            full_path = file_item["full_path"]
            record_id = f"img_{idx:05d}"

            # Validate image & extract technical metadata
            val_info = ImageValidator.validate_and_extract_metadata(full_path)

            if not val_info["valid"]:
                logger.warning(
                    f"Invalid file [{file_item['relative_path']}]: {val_info['invalid_reason']}"
                )

            record = {
                "id": record_id,
                "path": file_item["relative_path"],
                "filename": file_item["filename"],
                "label": file_item["label"],
                "source": file_item["source"],
                "extension": file_item["extension"],
                "size_bytes": val_info["size_bytes"],
                "width": val_info["width"],
                "height": val_info["height"],
                "mode": val_info["mode"],
                "valid": val_info["valid"],
                "invalid_reason": val_info["invalid_reason"],
                "duplicate": False,
                "full_path": full_path  # Temporary for hashing
            }
            raw_records.append(record)

        # Content Hash Deduplication
        logger.info("Performing content hash deduplication...")
        deduplicator = ImageDeduplicator()
        processed_records = deduplicator.process_records(raw_records)

        # Compute Summary Statistics
        summary = DatasetStatisticsCalculator.compute_summary(processed_records)
        summary["generated_at"] = datetime.now(timezone.utc).isoformat()
        summary["dataset_root"] = str(self.dataset_dir)

        # Remove absolute full_path before exporting index to ensure portability
        final_images: List[Dict[str, Any]] = []
        for rec in processed_records:
            clean_rec = {k: v for k, v in rec.items() if k != "full_path"}
            final_images.append(clean_rec)

        return {
            "summary": summary,
            "images": final_images
        }

    def save_index(self, index_data: Dict[str, Any], output_path: str | Path = None) -> Path:
        """
        Saves the structured index dictionary to a JSON file.
        """
        target_path = Path(output_path).resolve() if output_path else self.output_index_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Dataset index successfully saved to: {target_path}")
        return target_path

    def process(self) -> Dict[str, Any]:
        """
        Executes full dataset indexing pipeline and writes the output index file.
        """
        index_data = self.build_index()
        self.save_index(index_data)

        summary = index_data.get("summary", {})
        logger.info("=== Dataset Summary ===")
        logger.info(f"Total Images:    {summary.get('total_images', 0)}")
        logger.info(f"Valid Images:    {summary.get('valid_images', 0)}")
        logger.info(f"Invalid Images:  {summary.get('invalid_images', 0)}")
        logger.info(f"Human Count:     {summary.get('human_images', 0)}")
        logger.info(f"AI Count:        {summary.get('ai_images', 0)}")
        logger.info(f"Mixed Count:     {summary.get('mixed_images', 0)}")
        logger.info(f"Duplicates:      {summary.get('duplicate_images', 0)}")
        logger.info("=======================")

        return index_data


def main():
    manager = DatasetManager()
    manager.process()


if __name__ == "__main__":
    main()
