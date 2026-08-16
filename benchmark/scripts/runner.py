"""
Benchmark Runner Module
Orchestrates execution of benchmark passes.
"""
import os
import sys
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root and ai-service to sys.path if not present
project_root = Path(__file__).resolve().parent.parent.parent
ai_service_dir = project_root / "ai-service"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

from services.image_analyzer import analyze_image_authenticity
from models.model_manager import model_manager
from benchmark.scripts.dataset_manager import DatasetManager

logging.basicConfig(
    level=logging.INFO,
    format="[BenchmarkRunner] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BenchmarkRunner")


class BenchmarkRunner:
    """
    Executes benchmark evaluations by passing dataset images through
    the existing AI Image Forensics Engine and capturing raw predictions.
    """

    def __init__(
        self,
        index_path: str | Path = None,
        output_dir: str | Path = None,
        model: str = "primary",
        limit: Optional[int] = None,
        source: Optional[str] = None,
        label: Optional[str] = None,
        include_duplicates: bool = False,
        include_invalid: bool = False
    ):
        self.project_root = project_root
        self.index_path = Path(index_path).resolve() if index_path else (project_root / "benchmark" / "results" / "dataset_index.json")
        self.output_dir = Path(output_dir).resolve() if output_dir else (project_root / "benchmark" / "results")
        self.model_setting = model or "primary"
        self.limit = limit
        self.source_filter = source
        self.label_filter = label
        self.include_duplicates = include_duplicates
        self.include_invalid = include_invalid

    def load_or_generate_index(self) -> Dict[str, Any]:
        """
        Loads dataset_index.json. If missing, automatically generates it using DatasetManager.
        """
        if not self.index_path.exists():
            logger.info(f"Dataset index not found at {self.index_path}. Triggering DatasetManager...")
            dataset_dir = self.project_root / "benchmark" / "datasets"
            manager = DatasetManager(dataset_dir=dataset_dir, output_index_path=self.index_path)
            return manager.process()

        with open(self.index_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def resolve_image_path(self, record_path: str) -> Path:
        """
        Resolves relative or absolute image path to a valid Path on disk.
        """
        p = Path(record_path)
        if p.is_absolute() and p.exists():
            return p

        # Check relative to dataset base dir (parent of results folder)
        base_dir = self.index_path.parent.parent
        p_base = base_dir / record_path
        if p_base.exists():
            return p_base

        # Strip leading 'datasets/' if present and check under base_dir / 'datasets'
        clean_rel = record_path.lstrip("/\\")
        if clean_rel.startswith("datasets/") or clean_rel.startswith("datasets\\"):
            stripped = clean_rel[9:]
            p_strip = base_dir / "datasets" / stripped
            if p_strip.exists():
                return p_strip

        # Check relative to project root
        p1 = self.project_root / record_path
        if p1.exists():
            return p1

        # Check relative to benchmark directory
        p2 = self.project_root / "benchmark" / record_path
        if p2.exists():
            return p2

        return p_base

    def filter_records(self, all_images: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], int]:
        """
        Filters dataset index records based on validation, duplicates, label, source, and limit.
        Returns (selected_records, skipped_count).
        """
        selected: List[Dict[str, Any]] = []
        skipped = 0

        for rec in all_images:
            if not self.include_invalid and not rec.get("valid", True):
                skipped += 1
                continue

            if not self.include_duplicates and rec.get("duplicate", False):
                skipped += 1
                continue

            if self.label_filter and rec.get("label") != self.label_filter:
                skipped += 1
                continue

            if self.source_filter and rec.get("source") != self.source_filter:
                skipped += 1
                continue

            selected.append(rec)

            if self.limit is not None and len(selected) >= self.limit:
                break

        return selected, skipped

    def run_single_model_pass(self, model_key: str, selected_images: List[Dict[str, Any]], skipped_count: int) -> Dict[str, Any]:
        """
        Executes a benchmark run pass for a specific model key.
        """
        # Set primary model in environment for model_manager
        old_primary = os.environ.get("PRIMARY_IMAGE_MODEL")
        if model_key != "primary":
            os.environ["PRIMARY_IMAGE_MODEL"] = model_key

        model_name = model_manager.registry.get(model_key, getattr(model_manager, 'registry', {}).get('hf_vit_deepfake')).name if model_key in model_manager.registry else "Primary Image Model"

        logger.info(f"Starting Benchmark Pass for Model: '{model_key}' ({model_name})")
        logger.info(f"Selected Images: {len(selected_images)} | Skipped: {skipped_count}")

        raw_results: List[Dict[str, Any]] = []
        success_count = 0
        failed_count = 0
        total_inference_time = 0.0

        run_start_time = time.time()

        for idx, rec in enumerate(selected_images, start=1):
            rel_path = rec.get("path", "")
            img_path = self.resolve_image_path(rel_path)

            logger.info(f"[{idx}/{len(selected_images)}] Processing: {rel_path} | Model: {model_key}")

            t0 = time.time()
            ts_now = datetime.now(timezone.utc).isoformat()

            if not img_path.exists():
                elapsed_ms = int((time.time() - t0) * 1000)
                failed_count += 1
                result_item = {
                    "id": rec.get("id"),
                    "path": rel_path,
                    "filename": rec.get("filename"),
                    "ground_truth": rec.get("label"),
                    "source": rec.get("source"),
                    "predicted_label": None,
                    "ai_probability": None,
                    "human_probability": None,
                    "confidence": None,
                    "risk_level": None,
                    "model_name": model_name,
                    "inference_time_ms": elapsed_ms,
                    "success": False,
                    "error": f"Image file not found on disk: {img_path}",
                    "error_type": "FileNotFoundError",
                    "timestamp": ts_now
                }
                raw_results.append(result_item)
                logger.error(f"  └─ FAILED: File not found ({elapsed_ms}ms)")
                continue

            try:
                with open(img_path, "rb") as f:
                    image_bytes = f.read()

                if len(image_bytes) == 0:
                    raise ValueError("Zero-byte file content")

                # Pass image bytes to existing Image Forensics Engine
                detection_response = analyze_image_authenticity(image_bytes)
                elapsed_ms = int((time.time() - t0) * 1000)
                total_inference_time += elapsed_ms

                ai_prob = float(detection_response.get("aiProbability", 0.0))
                human_prob = float(detection_response.get("humanProbability", 100.0 - ai_prob))
                morph_prob = float(detection_response.get("morphProbability", 0.0))

                predicted_label = "ai" if max(ai_prob, morph_prob) >= 50.0 else "human"
                detected_model_name = detection_response.get("provider_used", model_name)

                result_item = {
                    "id": rec.get("id"),
                    "path": rel_path,
                    "filename": rec.get("filename"),
                    "ground_truth": rec.get("label"),
                    "source": rec.get("source"),
                    "predicted_label": predicted_label,
                    "ai_probability": ai_prob,
                    "human_probability": human_prob,
                    "confidence": detection_response.get("confidence"),
                    "risk_level": detection_response.get("risk_level"),
                    "model_name": detected_model_name,
                    "inference_time_ms": elapsed_ms,
                    "success": True,
                    "error": None,
                    "error_type": None,
                    "timestamp": ts_now
                }
                success_count += 1
                raw_results.append(result_item)
                logger.info(f"  └─ SUCCESS ({elapsed_ms}ms) | Predicted: {predicted_label} ({ai_prob}% AI)")

            except Exception as err:
                elapsed_ms = int((time.time() - t0) * 1000)
                failed_count += 1
                result_item = {
                    "id": rec.get("id"),
                    "path": rel_path,
                    "filename": rec.get("filename"),
                    "ground_truth": rec.get("label"),
                    "source": rec.get("source"),
                    "predicted_label": None,
                    "ai_probability": None,
                    "human_probability": None,
                    "confidence": None,
                    "risk_level": None,
                    "model_name": model_name,
                    "inference_time_ms": elapsed_ms,
                    "success": False,
                    "error": str(err),
                    "error_type": err.__class__.__name__,
                    "timestamp": ts_now
                }
                raw_results.append(result_item)
                logger.error(f"  └─ FAILED ({elapsed_ms}ms): {err.__class__.__name__} - {err}")

        # Restore env var
        if old_primary is not None:
            os.environ["PRIMARY_IMAGE_MODEL"] = old_primary
        elif "PRIMARY_IMAGE_MODEL" in os.environ:
            del os.environ["PRIMARY_IMAGE_MODEL"]

        total_duration_sec = round(time.time() - run_start_time, 2)
        avg_inference_ms = round(total_inference_time / max(1, success_count), 2)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"run_{timestamp_str}_{model_key}"

        run_output = {
            "summary": {
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_key": model_key,
                "model_name": model_name,
                "total_selected": len(selected_images),
                "successful": success_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "total_duration_sec": total_duration_sec,
                "avg_inference_time_ms": avg_inference_ms,
                "filters": {
                    "limit": self.limit,
                    "source": self.source_filter,
                    "label": self.label_filter
                }
            },
            "results": raw_results
        }

        # Save results to JSON files
        self.output_dir.mkdir(parents=True, exist_ok=True)
        run_file = self.output_dir / f"benchmark_run_{timestamp_str}_{model_key}.json"
        latest_file = self.output_dir / "latest_run.json"

        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(run_output, f, indent=2, ensure_ascii=False)

        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(run_output, f, indent=2, ensure_ascii=False)

        logger.info("\n======================================================")
        logger.info("Benchmark Run Summary")
        logger.info("======================================================")
        logger.info(f"Run ID:             {run_id}")
        logger.info(f"Model Key:          {model_key}")
        logger.info(f"Model Name:         {model_name}")
        logger.info(f"Total Selected:     {len(selected_images)}")
        logger.info(f"Successful:         {success_count}")
        logger.info(f"Failed:             {failed_count}")
        logger.info(f"Skipped:            {skipped_count}")
        logger.info(f"Total Duration:     {total_duration_sec}s")
        logger.info(f"Avg Time/Image:     {avg_inference_ms}ms")
        logger.info(f"Saved Result:       {run_file}")
        logger.info("======================================================\n")

        return run_output

    def run(self) -> List[Dict[str, Any]]:
        """
        Executes benchmark run across specified model(s).
        Returns list of run results.
        """
        index_data = self.load_or_generate_index()
        all_images = index_data.get("images", [])

        selected_images, skipped_count = self.filter_records(all_images)

        models_to_run: List[str] = []
        if self.model_setting == "all":
            models_to_run = list(model_manager.registry.keys())
        elif self.model_setting == "primary" or not self.model_setting:
            primary_key = os.getenv("PRIMARY_IMAGE_MODEL", "hf_vit_deepfake")
            models_to_run = [primary_key]
        else:
            models_to_run = [self.model_setting]

        all_runs: List[Dict[str, Any]] = []
        for model_key in models_to_run:
            run_res = self.run_single_model_pass(model_key, selected_images, skipped_count)
            all_runs.append(run_res)

        return all_runs
