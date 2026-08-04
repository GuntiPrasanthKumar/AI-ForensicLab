import os
import sys
import time
import json
import csv
import shutil
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

# Ensure root ai-service is in python path
AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_SERVICE_DIR not in sys.path:
    sys.path.append(AI_SERVICE_DIR)

from models.model_manager import model_manager
from services.image_analyzer import analyze_image_authenticity
from benchmark.scripts.dataset_generator import populate_all_datasets
from benchmark.metrics.metric_calculator import MetricCalculator

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(BENCHMARK_DIR, "datasets")
REPORTS_DIR = os.path.join(BENCHMARK_DIR, "reports")
ERRORS_DIR = os.path.join(REPORTS_DIR, "errors")

os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(ERRORS_DIR, exist_ok=True)

class BenchmarkEvaluator:
    """
    Automated Benchmark & Validation Laboratory Engine.
    Performs research-quality multi-model evaluation across taxonomy dataset categories.
    Captures misclassified error logs, ranks model leaderboards, and exports JSON, CSV, PDF, and summary.md.
    """

    def __init__(self):
        populate_all_datasets(3)

    def run_benchmark(self, model_keys: List[str] = None, categories: List[str] = None) -> Dict[str, Any]:
        """
        Runs automated benchmark evaluation.
        - model_keys: Optional list of model IDs (defaults to all in model_manager)
        - categories: Optional category filters (defaults to all)
        """
        if not model_keys:
            model_keys = list(model_manager.registry.keys())

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n=======================================================")
        print(f" AI Forensic Lab - Benchmark Laboratory Suite ({len(model_keys)} Models)")
        print(f"=======================================================\n")

        model_results = {}
        best_model_key = None
        best_composite_score = -1.0

        for key in model_keys:
            print(f"[Benchmark Laboratory] Evaluating Model: '{key}'...")
            result = self._evaluate_single_model(key, categories)
            model_results[key] = result

            # Rank model by composite score: 0.6 * F1 + 0.4 * ROC-AUC
            metrics = result["metrics"]
            composite = (0.6 * metrics["f1_score"]) + (0.4 * (metrics["roc_auc"] * 100.0))
            result["composite_score"] = round(composite, 2)

            if composite > best_composite_score:
                best_composite_score = composite
                best_model_key = key

        summary = {
            "benchmark_timestamp": timestamp,
            "models_evaluated": len(model_keys),
            "best_model": {
                "key": best_model_key,
                "name": model_results[best_model_key]["model_name"],
                "composite_score": best_composite_score
            },
            "model_results": model_results
        }

        # 1. Export JSON Report
        json_file = os.path.join(REPORTS_DIR, f"benchmark_{timestamp}.json")
        self._export_json(summary, json_file)

        # 2. Export CSV Report
        csv_file = os.path.join(REPORTS_DIR, f"benchmark_{timestamp}.csv")
        self._export_csv(summary, csv_file)

        # 3. Export PDF Report
        pdf_file = os.path.join(REPORTS_DIR, f"benchmark_{timestamp}.pdf")
        self._export_pdf(summary, pdf_file)

        # 4. Export summary.md Report
        md_file = os.path.join(REPORTS_DIR, f"summary_{timestamp}.md")
        self._export_markdown(summary, md_file)

        summary["generated_reports"] = {
            "json": json_file,
            "csv": csv_file,
            "pdf": pdf_file,
            "markdown": md_file,
            "errors_dir": ERRORS_DIR
        }

        print(f"\n=======================================================")
        print(f" Benchmark Complete! Leaderboard Winner: '{summary['best_model']['name']}'")
        print(f" Generated Reports:")
        print(f" - JSON    : {os.path.basename(json_file)}")
        print(f" - CSV     : {os.path.basename(csv_file)}")
        print(f" - PDF     : {os.path.basename(pdf_file)}")
        print(f" - Markdown: {os.path.basename(md_file)}")
        print(f"=======================================================\n")

        return summary

    def _evaluate_single_model(self, model_key: str, categories: List[str] = None) -> Dict[str, Any]:
        """Runs dataset evaluation pipeline for a single model."""
        os.environ["PRIMARY_IMAGE_MODEL"] = model_key

        model_ref = model_manager.registry.get(model_key)
        t_load_0 = time.time()
        if model_ref and not model_ref.is_loaded:
            model_ref.load()
        load_time_ms = (time.time() - t_load_0) * 1000.0

        predictions = []

        # Scan Human categories (Ground Truth = 0)
        human_base = os.path.join(DATASETS_DIR, "human")
        if os.path.exists(human_base):
            for cat_name in os.listdir(human_base):
                if categories and cat_name not in categories:
                    continue
                cat_path = os.path.join(human_base, cat_name)
                if os.path.isdir(cat_path):
                    for fname in os.listdir(cat_path):
                        if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            predictions.append(self._process_image_item(os.path.join(cat_path, fname), fname, cat_name, 0))

        # Scan AI categories (Ground Truth = 1)
        ai_base = os.path.join(DATASETS_DIR, "ai")
        if os.path.exists(ai_base):
            for cat_name in os.listdir(ai_base):
                if categories and cat_name not in categories:
                    continue
                cat_path = os.path.join(ai_base, cat_name)
                if os.path.isdir(cat_path):
                    for fname in os.listdir(cat_path):
                        if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            predictions.append(self._process_image_item(os.path.join(cat_path, fname), fname, cat_name, 1))

        # Compute complete statistical metrics
        res = MetricCalculator.compute_all_metrics(predictions, load_time_ms=load_time_ms)
        res["model_key"] = model_key
        res["model_name"] = model_ref.name if model_ref else model_key

        # Save failed predictions to reports/errors/
        for mis in res.get("misclassified_images", []):
            self._save_error_diagnostic(model_key, mis)

        return res

    def _process_image_item(self, filepath: str, filename: str, category: str, ground_truth: int) -> Dict[str, Any]:
        """Processes a single dataset image through detection pipeline."""
        with open(filepath, "rb") as fh:
            img_bytes = fh.read()

        t0 = time.time()
        res = analyze_image_authenticity(img_bytes)
        elapsed_ms = (time.time() - t0) * 1000.0

        ai_prob = res.get("aiProbability", 50.0)
        pred_label = 1 if ai_prob >= 50.0 else 0

        return {
            "filepath": filepath,
            "filename": filename,
            "category": category,
            "ground_truth": ground_truth,
            "predicted_prob": ai_prob,
            "predicted_label": pred_label,
            "confidence": res.get("confidence", "Medium"),
            "inference_time_ms": elapsed_ms,
            "reasons": res.get("reasons", [])
        }

    def _save_error_diagnostic(self, model_key: str, error_item: Dict[str, Any]):
        """Saves misclassified image copy and diagnostic JSON into reports/errors/."""
        try:
            err_sub = os.path.join(ERRORS_DIR, model_key)
            os.makedirs(err_sub, exist_ok=True)

            fname = error_item["filename"]
            src_path = error_item["filepath"]
            dest_img = os.path.join(err_sub, fname)
            if os.path.exists(src_path) and not os.path.exists(dest_img):
                shutil.copy2(src_path, dest_img)

            json_dest = os.path.join(err_sub, f"{os.path.splitext(fname)[0]}_error.json")
            with open(json_dest, "w", encoding="utf-8") as fh:
                json.dump(error_item, fh, indent=2)

        except Exception as e:
            print(f"[Benchmark Evaluator] Error logging warning: {e}")

    def _export_json(self, data: Dict[str, Any], filepath: str):
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def _export_csv(self, data: Dict[str, Any], filepath: str):
        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Model Key", "Model Name", "Composite Score", "Accuracy (%)", "Precision (%)", "Recall (%)", "F1 Score (%)", "Specificity (%)", "FPR (%)", "FNR (%)", "ROC-AUC", "Avg Time (ms)", "Memory (MB)", "TP", "FP", "TN", "FN"])
            for m_key, m_data in data.get("model_results", {}).items():
                m = m_data["metrics"]
                cm = m_data["confusion_matrix"]
                writer.writerow([
                    m_key, m_data["model_name"], m_data.get("composite_score", 0),
                    m["accuracy"], m["precision"], m["recall"], m["f1_score"],
                    m["specificity"], m["false_positive_rate"], m["false_negative_rate"],
                    m["roc_auc"], m["avg_inference_time_ms"], m["memory_usage_mb"],
                    cm["TP"], cm["FP"], cm["TN"], cm["FN"]
                ])

    def _export_pdf(self, data: Dict[str, Any], filepath: str):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            c = canvas.Canvas(filepath, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, 750, "AI Forensic Lab - Benchmark Evaluation Report")
            c.setFont("Helvetica", 10)
            c.drawString(50, 735, f"Timestamp: {data['benchmark_timestamp']} | Winner: {data['best_model']['name']}")
            c.line(50, 725, 550, 725)

            y = 700
            for m_key, m_data in data.get("model_results", {}).items():
                m = m_data["metrics"]
                cm = m_data["confusion_matrix"]

                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, f"Model: {m_data['model_name']} ({m_key}) [Composite: {m_data.get('composite_score', 0)}]")
                y -= 18

                c.setFont("Helvetica", 10)
                c.drawString(60, y, f"Accuracy: {m['accuracy']}% | Precision: {m['precision']}% | Recall: {m['recall']}% | F1: {m['f1_score']}%")
                y -= 15
                c.drawString(60, y, f"Specificity: {m['specificity']}% | FPR: {m['false_positive_rate']}% | FNR: {m['false_negative_rate']}% | ROC-AUC: {m['roc_auc']}")
                y -= 15
                c.drawString(60, y, f"Confusion: [TP: {cm['TP']}, FP: {cm['FP']}, TN: {cm['TN']}, FN: {cm['FN']}] | Time: {m['avg_inference_time_ms']}ms | Mem: {m['memory_usage_mb']}MB")
                y -= 25

                if y < 100:
                    c.showPage()
                    y = 750

            c.save()
        except ImportError:
            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write(f"AI Forensic Lab - Benchmark Report ({data['benchmark_timestamp']})\n")
                fh.write(json.dumps(data, indent=2))

    def _export_markdown(self, data: Dict[str, Any], filepath: str):
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(f"# AI Forensic Lab - Benchmark Summary Report\n\n")
            fh.write(f"- **Timestamp:** `{data['benchmark_timestamp']}`\n")
            fh.write(f"- **Evaluated Models:** `{data['models_evaluated']}`\n")
            fh.write(f"- **Leaderboard Winner:** `{data['best_model']['name']}` (Score: `{data['best_model']['composite_score']}`)\n\n")
            fh.write("## Model Performance Leaderboard\n\n")
            fh.write("| Model Name | Key | Accuracy | Precision | Recall | F1 Score | Specificity | FPR | FNR | ROC-AUC | Avg Time (ms) |\n")
            fh.write("|---|---|---|---|---|---|---|---|---|---|---|\n")

            for m_key, m_data in data.get("model_results", {}).items():
                m = m_data["metrics"]
                fh.write(f"| {m_data['model_name']} | `{m_key}` | {m['accuracy']}% | {m['precision']}% | {m['recall']}% | {m['f1_score']}% | {m['specificity']}% | {m['false_positive_rate']}% | {m['false_negative_rate']}% | {m['roc_auc']} | {m['avg_inference_time_ms']} ms |\n")
