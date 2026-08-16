"""
Model Comparison Engine Module
Compares vision models side-by-side with agreement metrics.
"""
import hashlib
import json
import math
import numpy as np
from typing import Dict, Any, List, Optional

from benchmark.metrics.evaluator import MetricsEngine
from benchmark.metrics.analysis_engine import EvaluationAnalysisEngine, safe_div, safe_mean


class ModelComparisonEngine:
    """
    Multi-Model Comparison Engine.
    Executes objective side-by-side evaluations across registered vision models using identical benchmark datasets.
    Calculates model metrics, inter-model agreement rates, disagreement samples, per-source breakdowns,
    and multi-metric composite rankings.
    """

    def __init__(self, min_source_samples: int = 3):
        self.min_source_samples = min_source_samples

    def compare_model_runs(
        self,
        runs_data: List[Dict[str, Any]],
        dataset_name: str = "dataset_index.json",
        dataset_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Processes a list of raw benchmark run outputs (one per model) and produces a multi-model comparison report.
        """
        dataset_hash = None
        if dataset_bytes:
            dataset_hash = hashlib.sha256(dataset_bytes).hexdigest()[:12]

        models_dict: Dict[str, Dict[str, Any]] = {}
        model_keys: List[str] = []
        raw_items_by_model: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # 1. Process each model run through Metrics Engine & Evaluation Analysis Engine
        for run in runs_data:
            summary = run.get("summary", {})
            m_key = summary.get("model_key") or "unknown_model"
            m_name = summary.get("model_name") or m_key
            results = run.get("results", [])

            model_keys.append(m_key)

            # Check model availability
            successful_cnt = summary.get("successful", 0)
            failed_cnt = summary.get("failed", 0)
            total_cnt = summary.get("total_selected", len(results))

            is_available = True
            unavail_reason = None

            if total_cnt > 0 and successful_cnt == 0:
                is_available = False
                first_err = next((r.get("error") for r in results if r.get("error")), "All inferences failed")
                unavail_reason = f"Model execution failed on all samples: {first_err}"

            # Compute metrics
            metrics_out = MetricsEngine.compute_all_metrics(run)
            analysis_out = EvaluationAnalysisEngine(min_source_samples=self.min_source_samples).analyze(metrics_out, run)

            clf = metrics_out.get("classification_metrics", {})
            err = analysis_out.get("error_analysis", {})
            perf = metrics_out.get("latency_and_performance", {})
            conf_m = metrics_out.get("confidence_analysis", {})

            # Compute average AI probability
            ai_probs = [
                r.get("ai_probability") for r in results
                if r.get("success", True) and r.get("ai_probability") is not None
            ]
            avg_ai_prob = safe_mean(ai_probs, default=0.0)

            models_dict[m_key] = {
                "model_key": m_key,
                "model_name": m_name,
                "available": is_available,
                "unavailable_reason": unavail_reason,
                "samples": total_cnt,
                "successful_samples": successful_cnt,
                "failed_samples": failed_cnt,
                "metrics": {
                    "accuracy": clf.get("accuracy", 0.0),
                    "precision": clf.get("precision", 0.0),
                    "recall": clf.get("recall", 0.0),
                    "f1_score": clf.get("f1_score", 0.0),
                    "specificity": clf.get("specificity", 0.0),
                    "false_positive_rate": err.get("false_positive_rate", 0.0),
                    "false_negative_rate": err.get("false_negative_rate", 0.0),
                    "roc_auc": analysis_out.get("model_level_analysis", {}).get("models", [{}])[0].get("roc_auc"),
                    "average_ai_probability": avg_ai_prob
                },
                "performance": {
                    "average_inference_time_ms": perf.get("mean_ms", 0.0),
                    "median_inference_time_ms": perf.get("p50_ms", 0.0),
                    "minimum_inference_time_ms": perf.get("min_ms", 0),
                    "maximum_inference_time_ms": perf.get("max_ms", 0),
                    "throughput_images_per_sec": perf.get("throughput_images_per_sec", 0.0)
                },
                "failure_rate": safe_div(failed_cnt, total_cnt) if total_cnt > 0 else 0.0,
                "source_breakdown": analysis_out.get("source_level_analysis", {})
            }

            # Map raw item results by image ID for agreement analysis
            items_map: Dict[str, Dict[str, Any]] = {}
            for r in results:
                img_id = r.get("id") or r.get("filename")
                if img_id:
                    items_map[img_id] = r
            raw_items_by_model[m_key] = items_map

        # 2. Compute Model Agreement & Disagreement Samples
        all_image_ids = set()
        for m_map in raw_items_by_model.values():
            all_image_ids.update(m_map.keys())

        agree_all_ai = 0
        agree_all_human = 0
        disagreements_cnt = 0
        evaluated_images_cnt = 0

        disagreement_samples: List[Dict[str, Any]] = []
        model_agreement_counts: Dict[str, int] = {m: 0 for m in model_keys}

        for img_id in sorted(all_image_ids):
            preds: Dict[str, Dict[str, Any]] = {}
            labels_set = set()
            gt_label = None

            for m_key in model_keys:
                r_item = raw_items_by_model[m_key].get(img_id)
                if r_item and r_item.get("success", True) and r_item.get("predicted_label"):
                    p_label = r_item.get("predicted_label")
                    labels_set.add(p_label)
                    if not gt_label:
                        gt_label = r_item.get("ground_truth")

                    preds[m_key] = {
                        "predicted_label": p_label,
                        "ai_probability": r_item.get("ai_probability"),
                        "confidence": r_item.get("confidence")
                    }

            if len(preds) < 2:
                continue  # Need at least 2 model predictions to assess agreement

            evaluated_images_cnt += 1
            rel_path = next((raw_items_by_model[m][img_id].get("path") for m in preds if img_id in raw_items_by_model[m]), img_id)
            fname = next((raw_items_by_model[m][img_id].get("filename") for m in preds if img_id in raw_items_by_model[m]), img_id)

            if len(labels_set) == 1:
                common_label = list(labels_set)[0]
                if common_label == "ai":
                    agree_all_ai += 1
                elif common_label == "human":
                    agree_all_human += 1

                for m in preds:
                    model_agreement_counts[m] += 1
            else:
                disagreements_cnt += 1
                disagreement_samples.append({
                    "id": img_id,
                    "filename": fname,
                    "path": rel_path,
                    "ground_truth": gt_label,
                    "model_predictions": preds,
                    "agreeing_models_count": max([list(preds.values()).count(p) for p in preds.values()])
                })

        overall_agree_rate = safe_div(agree_all_ai + agree_all_human, evaluated_images_cnt)
        ai_agree_rate = safe_div(agree_all_ai, evaluated_images_cnt)
        human_agree_rate = safe_div(agree_all_human, evaluated_images_cnt)

        for m_key in model_keys:
            models_dict[m_key]["agreement_rate"] = safe_div(model_agreement_counts[m_key], evaluated_images_cnt)

        agreement_summary = {
            "evaluated_common_images": evaluated_images_cnt,
            "overall_agreement_rate": overall_agree_rate,
            "ai_agreement_rate": ai_agree_rate,
            "human_agreement_rate": human_agree_rate,
            "agree_all_ai_count": agree_all_ai,
            "agree_all_human_count": agree_all_human,
            "disagreement_count": disagreements_cnt
        }

        # 3. Per-Source Model Comparison
        all_sources = set()
        for m_data in models_dict.values():
            all_sources.update(m_data.get("source_breakdown", {}).keys())

        source_comparison: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for src in sorted(all_sources):
            source_comparison[src] = {}
            for m_key, m_data in models_dict.items():
                s_info = m_data.get("source_breakdown", {}).get(src, {})
                source_comparison[src][m_key] = {
                    "samples": s_info.get("sample_count", 0),
                    "accuracy": s_info.get("accuracy", 0.0),
                    "precision": s_info.get("precision", 0.0),
                    "recall": s_info.get("recall", 0.0),
                    "f1_score": s_info.get("f1_score", 0.0),
                    "false_positive_rate": s_info.get("false_positive_rate", 0.0),
                    "false_negative_rate": s_info.get("false_negative_rate", 0.0),
                    "has_sufficient_samples": s_info.get("has_sufficient_samples", False)
                }

        # 4. Multi-Metric Model Ranking System
        ranking_list = []
        warnings = []
        recommendations = []

        total_samples_max = max([m["samples"] for m in models_dict.values()], default=0)

        if total_samples_max < 5:
            warnings.append("Insufficient data to establish a statistically reliable model ranking (< 5 samples).")
            ranking_status = "insufficient_data"
        else:
            ranking_status = "ranked"
            for m_key, m_data in models_dict.items():
                if not m_data["available"]:
                    continue

                met = m_data["metrics"]
                perf = m_data["performance"]

                f1 = met.get("f1_score", 0.0)
                auc = met.get("roc_auc") if met.get("roc_auc") is not None else f1
                fpr = met.get("false_positive_rate", 0.0)
                fnr = met.get("false_negative_rate", 0.0)

                # Latency speed score (scale 0..1, where 0ms=1.0, 5000ms=0.0)
                mean_ms = perf.get("average_inference_time_ms", 0.0)
                speed_score = max(0.0, 1.0 - (mean_ms / 5000.0))

                # Multi-Metric Composite Score Weighting
                composite_score = round(
                    0.35 * f1 +
                    0.25 * auc +
                    0.15 * (1.0 - fpr) +
                    0.15 * (1.0 - fnr) +
                    0.10 * speed_score,
                    4
                )

                ranking_list.append({
                    "model_key": m_key,
                    "model_name": m_data["model_name"],
                    "composite_score": composite_score,
                    "f1_score": f1,
                    "roc_auc": met.get("roc_auc"),
                    "accuracy": met.get("accuracy", 0.0),
                    "false_positive_rate": fpr,
                    "false_negative_rate": fnr,
                    "mean_latency_ms": mean_ms
                })

            ranking_list.sort(key=lambda x: x["composite_score"], reverse=True)
            for idx, item in enumerate(ranking_list, start=1):
                item["rank"] = idx

        # Generate warnings and empirical recommendations
        if disagreements_cnt > 0:
            warnings.append(f"Model disagreement detected on {disagreements_cnt} image samples ({safe_div(disagreements_cnt, evaluated_images_cnt)*100:.1f}%).")
            recommendations.append("Inspect disagreement sample IDs to identify edge cases near decision boundaries.")

        if not warnings:
            warnings.append("No critical multi-model anomalies detected.")

        return {
            "comparison_metadata": {
                "dataset_id": dataset_name,
                "dataset_hash": dataset_hash,
                "total_evaluated_images": max([m["samples"] for m in models_dict.values()], default=0),
                "models_count": len(models_dict),
                "models_keys": model_keys,
                "ranking_status": ranking_status
            },
            "models": models_dict,
            "agreement": agreement_summary,
            "disagreements": disagreement_samples,
            "source_comparison": source_comparison,
            "ranking": ranking_list if ranking_status == "ranked" else "insufficient_data",
            "warnings": warnings,
            "recommendations": recommendations
        }
