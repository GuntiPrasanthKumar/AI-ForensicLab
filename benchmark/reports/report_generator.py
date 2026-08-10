import csv
import json
import math
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from fpdf import FPDF

logging.basicConfig(
    level=logging.INFO,
    format="[ReportGenerator] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ReportGenerator")


def sanitize_pdf_text(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        "\u2014": " - ",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "*",
        "\u26a0": "[WARNING]",
        "\ud83d\udca1": "[RECOMMENDATION]"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class ForensicBenchmarkPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 110, 120)
        self.cell(0, 6, sanitize_pdf_text("AI FORENSIC LAB - BENCHMARK REPORT"), border=0, new_x="LMARGIN", new_y="NEXT", align="R")
        self.set_draw_color(210, 215, 220)
        self.line(10, 16, 200, 16)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 135, 140)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


class ReportGenerator:
    """
    Benchmark Reporting Engine.
    Consumes outputs from Dataset Manager, Benchmark Runner, Metrics Engine,
    and Evaluation Analysis to produce JSON, CSV, Markdown, and PDF reports.
    """

    def __init__(
        self,
        run_data: Optional[Dict[str, Any]] = None,
        metrics_data: Optional[Dict[str, Any]] = None,
        analysis_data: Optional[Dict[str, Any]] = None
    ):
        self.run_data = run_data or {}
        self.metrics_data = metrics_data or {}
        self.analysis_data = analysis_data or {}

    @classmethod
    def load_from_files(
        cls,
        run_file: Optional[Path | str] = None,
        metrics_file: Optional[Path | str] = None,
        analysis_file: Optional[Path | str] = None
    ) -> "ReportGenerator":
        """
        Loads report inputs from filesystem paths.
        Raises FileNotFoundError if required files do not exist.
        """
        def read_json_if_exists(p_str: Optional[Path | str], req_name: str) -> Dict[str, Any]:
            if not p_str:
                return {}
            p = Path(p_str).resolve()
            if not p.exists():
                raise FileNotFoundError(f"Required report input file missing: '{req_name}' at path: {p}")
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)

        run_d = read_json_if_exists(run_file, "Run Output (run.json)")
        metrics_d = read_json_if_exists(metrics_file, "Metrics Output (metrics.json)")
        analysis_d = read_json_if_exists(analysis_file, "Evaluation Analysis (analysis.json)")

        return cls(run_data=run_d, metrics_data=metrics_d, analysis_data=analysis_d)

    def generate_report_dict(self) -> Dict[str, Any]:
        """
        Consolidates and structures all evaluation inputs into a unified report dictionary.
        """
        meta_summary = self.analysis_data.get("summary_metadata", {})
        meta_metrics = self.metrics_data.get("metadata", {})
        meta_run = self.run_data.get("summary", {})

        run_id = meta_summary.get("run_id") or meta_metrics.get("run_id") or meta_run.get("run_id") or "run_latest"
        model_name = meta_summary.get("model_name") or meta_metrics.get("model_name") or meta_run.get("model_name") or "Primary Model"
        model_key = meta_summary.get("model_key") or meta_metrics.get("model_key") or meta_run.get("model_key") or "primary"
        timestamp = meta_summary.get("timestamp") or meta_metrics.get("timestamp") or datetime.now(timezone.utc).isoformat()

        total_selected = meta_run.get("total_selected") or meta_summary.get("total_evaluated") or meta_metrics.get("total_selected") or 0
        successful = meta_run.get("successful") or meta_metrics.get("successful") or 0
        failed = meta_run.get("failed") or meta_metrics.get("failed") or 0
        skipped = meta_run.get("skipped") or meta_metrics.get("skipped") or 0

        cm_data = self.analysis_data.get("confusion_matrix", self.metrics_data.get("confusion_matrix", {}))
        raw_cm = cm_data.get("raw", cm_data)
        norm_cm = cm_data.get("normalized", {})

        clf_metrics = self.metrics_data.get("classification_metrics", {})
        err_analysis = self.analysis_data.get("error_analysis", {})
        db_balance = self.analysis_data.get("dataset_balance", {})
        perf_data = self.metrics_data.get("latency_and_performance", {})
        src_analysis = self.analysis_data.get("source_level_analysis", {})
        model_analysis = self.analysis_data.get("model_level_analysis", {})
        summary = self.analysis_data.get("analysis_summary", {})

        # Source breakdown distribution
        src_dist = {}
        for s_name, s_val in src_analysis.items():
            src_dist[s_name] = s_val.get("sample_count", 0)

        # Sanitize sensitive filesystem paths from error sample lists
        sanitized_fps = []
        for fp in err_analysis.get("false_positives", []):
            sanitized_fps.append({
                "id": fp.get("id"),
                "filename": fp.get("filename"),
                "ground_truth": fp.get("ground_truth"),
                "predicted_label": fp.get("predicted_label"),
                "ai_probability": fp.get("ai_probability"),
                "confidence": fp.get("confidence"),
                "source": fp.get("source")
            })

        sanitized_fns = []
        for fn in err_analysis.get("false_negatives", []):
            sanitized_fns.append({
                "id": fn.get("id"),
                "filename": fn.get("filename"),
                "ground_truth": fn.get("ground_truth"),
                "predicted_label": fn.get("predicted_label"),
                "ai_probability": fn.get("ai_probability"),
                "confidence": fn.get("confidence"),
                "source": fn.get("source")
            })

        return {
            "report_metadata": {
                "report_title": "AI Forensic Lab — Image Forensics Benchmark Report",
                "run_id": run_id,
                "timestamp": timestamp,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "primary_model_name": model_name,
                "primary_model_key": model_key
            },
            "executive_summary": {
                "dataset_size": total_selected,
                "successful_analyses": successful,
                "failed_analyses": failed,
                "human_samples": db_balance.get("human_count", raw_cm.get("true_negative", 0) + raw_cm.get("false_positive", 0)),
                "ai_samples": db_balance.get("ai_count", raw_cm.get("true_positive", 0) + raw_cm.get("false_negative", 0)),
                "overall_accuracy": clf_metrics.get("accuracy", 0.0),
                "f1_score": clf_metrics.get("f1_score", 0.0),
                "primary_model": model_name,
                "average_inference_time_ms": perf_data.get("mean_ms", 0.0)
            },
            "dataset": {
                "total_images": total_selected,
                "valid_images": successful,
                "invalid_images": skipped,
                "skipped_images": skipped,
                "human_count": db_balance.get("human_count", 0),
                "ai_count": db_balance.get("ai_count", 0),
                "class_distribution": {
                    "human_percentage": db_balance.get("human_percentage", 0.0),
                    "ai_percentage": db_balance.get("ai_percentage", 0.0)
                },
                "source_distribution": src_dist,
                "duplicate_count": 0
            },
            "confusion_matrix": {
                "raw": {
                    "true_positive": raw_cm.get("true_positive", raw_cm.get("tp", 0)),
                    "true_negative": raw_cm.get("true_negative", raw_cm.get("tn", 0)),
                    "false_positive": raw_cm.get("false_positive", raw_cm.get("fp", 0)),
                    "false_negative": raw_cm.get("false_negative", raw_cm.get("fn", 0))
                },
                "normalized": norm_cm
            },
            "metrics": {
                "accuracy": clf_metrics.get("accuracy", 0.0),
                "precision": clf_metrics.get("precision", 0.0),
                "recall": clf_metrics.get("recall", 0.0),
                "f1_score": clf_metrics.get("f1_score", 0.0),
                "specificity": clf_metrics.get("specificity", 0.0),
                "false_positive_rate": err_analysis.get("false_positive_rate", 0.0),
                "false_negative_rate": err_analysis.get("false_negative_rate", 0.0),
                "roc_auc": model_analysis.get("models", [{}])[0].get("roc_auc")
            },
            "performance": {
                "average_inference_time_ms": perf_data.get("mean_ms", 0.0),
                "median_inference_time_ms": perf_data.get("p50_ms", 0.0),
                "minimum_inference_time_ms": perf_data.get("min_ms", 0.0),
                "maximum_inference_time_ms": perf_data.get("max_ms", 0.0),
                "failure_rate": safe_div_static(failed, total_selected)
            },
            "error_analysis": {
                "total_false_positives": err_analysis.get("total_false_positives", len(sanitized_fps)),
                "total_false_negatives": err_analysis.get("total_false_negatives", len(sanitized_fns)),
                "high_confidence_errors": self.analysis_data.get("error_categories", {}).get("high_confidence_errors", {}).get("count", 0),
                "failed_analyses": failed,
                "false_positives": sanitized_fps,
                "false_negatives": sanitized_fns
            },
            "source_analysis": src_analysis,
            "model_comparison": model_analysis.get("models", []),
            "warnings": summary.get("warnings", []),
            "recommendations": summary.get("recommendations", [])
        }

    def generate_json_report(self, output_dir: Path, timestamp_str: str) -> Path:
        """Exports benchmark_report_<timestamp>.json and latest_report.json."""
        rep_data = self.generate_report_dict()
        file_path = output_dir / f"benchmark_report_{timestamp_str}.json"
        latest_file = output_dir / "latest_report.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rep_data, f, indent=2, ensure_ascii=False)

        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(rep_data, f, indent=2, ensure_ascii=False)

        return file_path

    def generate_csv_report(self, output_dir: Path, timestamp_str: str) -> Path:
        """Exports benchmark_metrics_<timestamp>.csv for model comparison table."""
        rep_data = self.generate_report_dict()
        file_path = output_dir / f"benchmark_metrics_{timestamp_str}.csv"
        models = rep_data.get("model_comparison", [])

        fieldnames = [
            "model", "samples", "accuracy", "precision", "recall", "f1",
            "specificity", "false_positive_rate", "false_negative_rate",
            "roc_auc", "average_inference_time_ms", "failure_rate"
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            if not models:
                # Fallback to single primary model metrics if model comparison is empty
                m_info = rep_data["metrics"]
                p_info = rep_data["performance"]
                e_info = rep_data["executive_summary"]
                writer.writerow({
                    "model": e_info.get("primary_model", "Primary Model"),
                    "samples": e_info.get("dataset_size", 0),
                    "accuracy": m_info.get("accuracy", 0.0),
                    "precision": m_info.get("precision", 0.0),
                    "recall": m_info.get("recall", 0.0),
                    "f1": m_info.get("f1_score", 0.0),
                    "specificity": m_info.get("specificity", 0.0),
                    "false_positive_rate": m_info.get("false_positive_rate", 0.0),
                    "false_negative_rate": m_info.get("false_negative_rate", 0.0),
                    "roc_auc": m_info.get("roc_auc", "N/A"),
                    "average_inference_time_ms": p_info.get("average_inference_time_ms", 0.0),
                    "failure_rate": p_info.get("failure_rate", 0.0)
                })
            else:
                m_info = rep_data["metrics"]
                for m in models:
                    writer.writerow({
                        "model": m.get("model_name", m.get("model_key")),
                        "samples": m.get("sample_count", 0),
                        "accuracy": m.get("accuracy", 0.0),
                        "precision": m.get("precision", 0.0),
                        "recall": m.get("recall", 0.0),
                        "f1": m.get("f1_score", 0.0),
                        "specificity": m_info.get("specificity", 0.0),
                        "false_positive_rate": m.get("false_positive_rate", 0.0),
                        "false_negative_rate": m.get("false_negative_rate", 0.0),
                        "roc_auc": m.get("roc_auc") if m.get("roc_auc") is not None else "N/A",
                        "average_inference_time_ms": m.get("avg_inference_time_ms", 0.0),
                        "failure_rate": m.get("failure_rate", 0.0)
                    })

        return file_path

    def generate_markdown_report(self, output_dir: Path, timestamp_str: str) -> Path:
        """Exports benchmark_report_<timestamp>.md and latest_report.md."""
        rep = self.generate_report_dict()
        meta = rep["report_metadata"]
        exec_s = rep["executive_summary"]
        ds = rep["dataset"]
        cm = rep["confusion_matrix"]["raw"]
        cm_n = rep["confusion_matrix"]["normalized"]
        m = rep["metrics"]
        p = rep["performance"]
        err = rep["error_analysis"]
        src = rep["source_analysis"]
        models = rep["model_comparison"]
        warns = rep["warnings"]
        recs = rep["recommendations"]

        lines = [
            f"# {meta['report_title']}",
            "",
            f"**Run ID:** `{meta['run_id']}` | **Generated:** `{meta['generated_at']}` | **Primary Model:** `{exec_s['primary_model']}`",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Dataset Size:** {exec_s['dataset_size']} images",
            f"- **Successful / Failed:** {exec_s['successful_analyses']} successful, {exec_s['failed_analyses']} failed",
            f"- **Class Breakdown:** {exec_s['human_samples']} Human photographs, {exec_s['ai_samples']} AI-generated images",
            f"- **Overall Performance:** **{exec_s['overall_accuracy'] * 100:.2f}% Accuracy** | **{exec_s['f1_score']:.4f} F1-Score**",
            f"- **Average Inference Speed:** {exec_s['average_inference_time_ms']:.1f} ms / image",
            "",
            "## 2. Dataset Summary",
            "",
            "| Metric | Count | Proportion |",
            "| :--- | :--- | :--- |",
            f"| Total Selected Images | {ds['total_images']} | 100.0% |",
            f"| Valid Images Evaluated | {ds['valid_images']} | {safe_div_static(ds['valid_images'], ds['total_images']) * 100:.1f}% |",
            f"| Skipped / Invalid | {ds['skipped_images']} | {safe_div_static(ds['skipped_images'], ds['total_images']) * 100:.1f}% |",
            f"| Human Photographs | {ds['human_count']} | {ds['class_distribution']['human_percentage']:.1f}% |",
            f"| AI-Generated Media | {ds['ai_count']} | {ds['class_distribution']['ai_percentage']:.1f}% |",
            "",
            "## 3. Confusion Matrix",
            "",
            "### Raw Predictions",
            "| Ground Truth \\ Predicted | Predicted Human | Predicted AI |",
            "| :--- | :--- | :--- |",
            f"| **Actual Human** | TN = **{cm['true_negative']}** | FP = **{cm['false_positive']}** |",
            f"| **Actual AI** | FN = **{cm['false_negative']}** | TP = **{cm['true_positive']}** |",
            "",
            "### Normalized Proportions",
            "| Ground Truth | Predicted Human % | Predicted AI % |",
            "| :--- | :--- | :--- |",
            f"| **Actual Human** | {cm_n.get('human_actual', {}).get('predicted_human', 0.0) * 100:.1f}% | {cm_n.get('human_actual', {}).get('predicted_ai', 0.0) * 100:.1f}% |",
            f"| **Actual AI** | {cm_n.get('ai_actual', {}).get('predicted_human', 0.0) * 100:.1f}% | {cm_n.get('ai_actual', {}).get('predicted_ai', 0.0) * 100:.1f}% |",
            "",
            "## 4. Classification Metrics",
            "",
            "| Metric | Value | Description |",
            "| :--- | :--- | :--- |",
            f"| **Accuracy** | `{m['accuracy']:.4f}` ({m['accuracy'] * 100:.2f}%) | Overall correct classification rate |",
            f"| **Precision** | `{m['precision']:.4f}` | Proportion of AI predictions that were truly AI |",
            f"| **Recall (Sensitivity)** | `{m['recall']:.4f}` | Proportion of actual AI images detected |",
            f"| **Specificity** | `{m['specificity']:.4f}` | Proportion of actual Human images detected |",
            f"| **F1 Score** | `{m['f1_score']:.4f}` | Harmonic mean of Precision and Recall |",
            f"| **False Positive Rate** | `{m['false_positive_rate']:.4f}` ({m['false_positive_rate'] * 100:.2f}%) | Rate of authentic images misclassified as AI |",
            f"| **False Negative Rate** | `{m['false_negative_rate']:.4f}` ({m['false_negative_rate'] * 100:.2f}%) | Rate of AI images missed |",
            f"| **ROC-AUC** | `{m['roc_auc'] if m['roc_auc'] is not None else 'N/A'}` | Area under ROC curve across decision thresholds |",
            "",
            "## 5. Performance & Telemetry",
            "",
            f"- **Average Inference Time:** {p['average_inference_time_ms']:.1f} ms",
            f"- **Median Latency (P50):** {p['median_inference_time_ms']:.1f} ms",
            f"- **Min / Max Latency:** {p['minimum_inference_time_ms']} ms / {p['maximum_inference_time_ms']} ms",
            f"- **Failure Rate:** {p['failure_rate'] * 100:.2f}%",
            "",
            "## 6. Error Analysis",
            "",
            f"- **Total False Positives:** {err['total_false_positives']}",
            f"- **Total False Negatives:** {err['total_false_negatives']}",
            f"- **High Confidence Misclassifications:** {err['high_confidence_errors']}",
            f"- **Failed Pipeline Inferences:** {err['failed_analyses']}",
            ""
        ]

        if err["false_positives"]:
            lines.append("### False Positive Samples (Human -> AI)")
            lines.append("| Sample ID | Filename | Source | AI Prob | Confidence |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for item in err["false_positives"]:
                lines.append(f"| `{item.get('id')}` | `{item.get('filename')}` | `{item.get('source')}` | {item.get('ai_probability')}% | {item.get('confidence')} |")
            lines.append("")

        if err["false_negatives"]:
            lines.append("### False Negative Samples (AI -> Human)")
            lines.append("| Sample ID | Filename | Source | AI Prob | Confidence |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for item in err["false_negatives"]:
                lines.append(f"| `{item.get('id')}` | `{item.get('filename')}` | `{item.get('source')}` | {item.get('ai_probability')}% | {item.get('confidence')} |")
            lines.append("")

        lines.extend([
            "## 7. Source-Level Analysis",
            "",
            "| Source | Samples | Accuracy | Precision | Recall | F1 | FPR | FNR | Avg AI Prob | Sufficiency |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ])

        for s_name, s_val in src.items():
            suff = "Sufficient" if s_val.get("has_sufficient_samples") else "Insufficient (<3)"
            acc_val = (s_val.get("accuracy") or 0.0)
            prec_val = (s_val.get("precision") or 0.0)
            rec_val = (s_val.get("recall") or 0.0)
            f1_val = (s_val.get("f1_score") or 0.0)
            fpr_val = (s_val.get("false_positive_rate") or 0.0)
            fnr_val = (s_val.get("false_negative_rate") or 0.0)
            prob_val = (s_val.get("avg_ai_probability") or 0.0)

            lines.append(
                f"| `{s_name}` | {s_val.get('sample_count', 0)} | {acc_val * 100:.1f}% | "
                f"{prec_val:.2f} | {rec_val:.2f} | {f1_val:.2f} | "
                f"{fpr_val * 100:.1f}% | {fnr_val * 100:.1f}% | "
                f"{prob_val:.1f}% | {suff} |"
            )

        lines.extend([
            "",
            "## 8. Model Comparison",
            "",
            "| Model | Samples | Accuracy | Precision | Recall | F1 | ROC-AUC | FPR | FNR | Avg Latency | Failure Rate |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ])

        if models:
            for mod in models:
                auc_val = f"{mod.get('roc_auc'):.4f}" if mod.get('roc_auc') is not None else "N/A"
                acc_val = (mod.get("accuracy") or 0.0)
                prec_val = (mod.get("precision") or 0.0)
                rec_val = (mod.get("recall") or 0.0)
                f1_val = (mod.get("f1_score") or 0.0)
                fpr_val = (mod.get("false_positive_rate") or 0.0)
                fnr_val = (mod.get("false_negative_rate") or 0.0)
                lat_val = (mod.get("avg_inference_time_ms") or 0.0)
                fail_val = (mod.get("failure_rate") or 0.0)

                lines.append(
                    f"| `{mod.get('model_name')}` | {mod.get('sample_count', 0)} | {acc_val * 100:.1f}% | "
                    f"{prec_val:.4f} | {rec_val:.4f} | {f1_val:.4f} | "
                    f"{auc_val} | {fpr_val * 100:.1f}% | {fnr_val * 100:.1f}% | "
                    f"{lat_val:.1f} ms | {fail_val * 100:.1f}% |"
                )

        lines.extend([
            "",
            "## 9. Evaluation Warnings",
            ""
        ])

        if warns:
            for w in warns:
                lines.append(f"- ⚠️ **WARNING:** {w}")
        else:
            lines.append("- No critical evaluation warnings flagged.")

        lines.extend([
            "",
            "## 10. Empirical Recommendations",
            ""
        ])

        if recs:
            for r in recs:
                lines.append(f"- 💡 **RECOMMENDATION:** {r}")
        else:
            lines.append("- Benchmark results indicate balanced performance across measured parameters.")

        lines.append("")

        file_path = output_dir / f"benchmark_report_{timestamp_str}.md"
        latest_file = output_dir / "latest_report.md"

        content_str = "\n".join(lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_str)

        with open(latest_file, "w", encoding="utf-8") as f:
            f.write(content_str)

        return file_path

    def generate_pdf_report(self, output_dir: Path, timestamp_str: str) -> Path:
        """Exports benchmark_report_<timestamp>.pdf."""
        rep = self.generate_report_dict()
        meta = rep["report_metadata"]
        exec_s = rep["executive_summary"]
        ds = rep["dataset"]
        cm = rep["confusion_matrix"]["raw"]
        cm_n = rep["confusion_matrix"]["normalized"]
        m = rep["metrics"]
        p = rep["performance"]
        src = rep["source_analysis"]
        warns = rep["warnings"]
        recs = rep["recommendations"]

        pdf = ForensicBenchmarkPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Title Section
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(20, 30, 40)
        pdf.cell(0, 10, sanitize_pdf_text(meta["report_title"]), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, sanitize_pdf_text(f"Run ID: {meta['run_id']}   |   Primary Model: {exec_s['primary_model']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, sanitize_pdf_text(f"Generated: {meta['generated_at'][:19].replace('T', ' ')} UTC"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # 1. Executive Summary
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 80, 150)
        pdf.cell(0, 8, sanitize_pdf_text("1. Executive Summary"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)

        exec_text = (
            f"Evaluated {exec_s['dataset_size']} benchmark images ({exec_s['human_samples']} Human, {exec_s['ai_samples']} AI) "
            f"using '{exec_s['primary_model']}'. Overall Accuracy reached {exec_s['overall_accuracy'] * 100:.2f}% "
            f"with F1-Score of {exec_s['f1_score']:.4f} and average inference latency of {exec_s['average_inference_time_ms']:.1f} ms."
        )
        pdf.multi_cell(0, 6, sanitize_pdf_text(exec_text))
        pdf.ln(4)

        # 2. Confusion Matrix Table
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 80, 150)
        pdf.cell(0, 8, sanitize_pdf_text("2. Confusion Matrix"), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(235, 240, 248)
        pdf.set_text_color(20, 30, 40)

        # Table Header
        pdf.cell(50, 7, sanitize_pdf_text("Actual / Predicted"), border=1, fill=True)
        pdf.cell(45, 7, sanitize_pdf_text("Predicted Human"), border=1, fill=True)
        pdf.cell(45, 7, sanitize_pdf_text("Predicted AI"), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        # Row 1: Actual Human
        pdf.cell(50, 7, sanitize_pdf_text("Actual Human"), border=1)
        pdf.cell(45, 7, sanitize_pdf_text(f"TN = {cm['true_negative']} ({cm_n.get('human_actual',{}).get('predicted_human',0)*100:.1f}%)"), border=1)
        pdf.cell(45, 7, sanitize_pdf_text(f"FP = {cm['false_positive']} ({cm_n.get('human_actual',{}).get('predicted_ai',0)*100:.1f}%)"), border=1, new_x="LMARGIN", new_y="NEXT")

        # Row 2: Actual AI
        pdf.cell(50, 7, sanitize_pdf_text("Actual AI"), border=1)
        pdf.cell(45, 7, sanitize_pdf_text(f"FN = {cm['false_negative']} ({cm_n.get('ai_actual',{}).get('predicted_human',0)*100:.1f}%)"), border=1)
        pdf.cell(45, 7, sanitize_pdf_text(f"TP = {cm['true_positive']} ({cm_n.get('ai_actual',{}).get('predicted_ai',0)*100:.1f}%)"), border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # 3. Key Metrics Table
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 80, 150)
        pdf.cell(0, 8, sanitize_pdf_text("3. Key Evaluation Metrics"), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(235, 240, 248)
        pdf.cell(60, 7, sanitize_pdf_text("Metric"), border=1, fill=True)
        pdf.cell(40, 7, sanitize_pdf_text("Value"), border=1, fill=True)
        pdf.cell(80, 7, sanitize_pdf_text("Description"), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        metrics_rows = [
            ("Accuracy", f"{m['accuracy'] * 100:.2f}%", "Overall correct classification rate"),
            ("Precision", f"{m['precision']:.4f}", "Proportion of AI predictions that were AI"),
            ("Recall (Sensitivity)", f"{m['recall']:.4f}", "Proportion of actual AI images detected"),
            ("Specificity", f"{m['specificity']:.4f}", "Proportion of actual Human images detected"),
            ("F1 Score", f"{m['f1_score']:.4f}", "Harmonic mean of Precision and Recall"),
            ("False Positive Rate", f"{m['false_positive_rate'] * 100:.2f}%", "Authentic human images misclassified as AI"),
            ("False Negative Rate", f"{m['false_negative_rate'] * 100:.2f}%", "AI-generated images missed"),
            ("ROC-AUC", f"{m['roc_auc']}" if m['roc_auc'] is not None else "N/A", "Area under ROC curve across thresholds")
        ]

        for name, val_s, desc_s in metrics_rows:
            pdf.cell(60, 6, sanitize_pdf_text(name), border=1)
            pdf.cell(40, 6, sanitize_pdf_text(val_s), border=1)
            pdf.cell(80, 6, sanitize_pdf_text(desc_s), border=1, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(5)

        # 4. Warnings & Recommendations
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 80, 150)
        pdf.cell(0, 8, sanitize_pdf_text("4. Evaluation Warnings & Recommendations"), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)

        if warns:
            for w in warns:
                pdf.multi_cell(0, 5, sanitize_pdf_text(f"[WARNING] {w}"))
                pdf.ln(1)
        else:
            pdf.cell(0, 5, sanitize_pdf_text("No critical warnings flagged."), new_x="LMARGIN", new_y="NEXT")

        pdf.ln(2)
        if recs:
            for r in recs:
                pdf.multi_cell(0, 5, sanitize_pdf_text(f"[RECOMMENDATION] {r}"))
                pdf.ln(1)
        else:
            pdf.cell(0, 5, sanitize_pdf_text("Performance is balanced across measured benchmark parameters."), new_x="LMARGIN", new_y="NEXT")

        file_path = output_dir / f"benchmark_report_{timestamp_str}.pdf"
        pdf.output(str(file_path))
        return file_path

    def generate_all_reports(self, output_dir: Path) -> Dict[str, Path]:
        """
        Generates JSON, CSV, Markdown, and PDF benchmark reports.
        Returns dictionary of created file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_p = self.generate_json_report(output_dir, timestamp_str)
        csv_p = self.generate_csv_report(output_dir, timestamp_str)
        md_p = self.generate_markdown_report(output_dir, timestamp_str)
        pdf_p = self.generate_pdf_report(output_dir, timestamp_str)

        logger.info(f"Generated Benchmark Reports in {output_dir}:")
        logger.info(f"  ├─ JSON: {json_p.name}")
        logger.info(f"  ├─ CSV:  {csv_p.name}")
        logger.info(f"  ├─ MD:   {md_p.name}")
        logger.info(f"  └─ PDF:  {pdf_p.name}")

        return {
            "json": json_p,
            "csv": csv_p,
            "markdown": md_p,
            "pdf": pdf_p
        }


def safe_div_static(num: float, den: float, default: float = 0.0) -> float:
    if den == 0 or math.isnan(den) or math.isnan(num):
        return default
    res = num / den
    if math.isnan(res) or math.isinf(res):
        return default
    return round(float(res), 4)
