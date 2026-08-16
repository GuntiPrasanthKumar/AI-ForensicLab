"""
Evaluation Analysis Engine Module
Analyzes model errors, dataset balance, and recommendations.
"""
import math
import numpy as np
from typing import Dict, Any, List, Optional


def safe_div(num: float, den: float, default: float = 0.0) -> float:
    """Safe division avoiding ZeroDivisionError, NaN, and Infinity."""
    if den == 0 or math.isnan(den) or math.isnan(num):
        return default
    res = num / den
    if math.isnan(res) or math.isinf(res):
        return default
    return round(float(res), 4)


def safe_mean(arr: List[float], default: float = 0.0) -> float:
    """Safe average calculation for a list of floats."""
    valid_vals = [v for v in arr if v is not None and not math.isnan(v)]
    if not valid_vals:
        return default
    return round(float(np.mean(valid_vals)), 2)


def compute_roc_auc(y_true: List[int], y_scores: List[float]) -> Optional[float]:
    """
    Computes ROC-AUC score using trapezoidal integration over sorted score thresholds.
    y_true: 1 for AI, 0 for Human.
    """
    if len(set(y_true)) < 2 or not y_scores or len(y_true) != len(y_scores):
        return None

    # Sort descending by score
    sorted_pairs = sorted(zip(y_scores, y_true), key=lambda x: x[0], reverse=True)
    
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos

    if n_pos == 0 or n_neg == 0:
        return None

    tpr_list = [0.0]
    fpr_list = [0.0]

    cur_tp = 0
    cur_fp = 0

    for score, target in sorted_pairs:
        if target == 1:
            cur_tp += 1
        else:
            cur_fp += 1
        tpr_list.append(cur_tp / n_pos)
        fpr_list.append(cur_fp / n_neg)

    # Trapezoidal rule integration
    auc = 0.0
    for i in range(1, len(fpr_list)):
        width = fpr_list[i] - fpr_list[i - 1]
        height = (tpr_list[i] + tpr_list[i - 1]) / 2.0
        auc += width * height

    return round(float(auc), 4)


class EvaluationAnalysisEngine:
    """
    Structured Evaluation Analysis Engine.
    Turns benchmark metrics and raw execution logs into deep diagnostic insights,
    confusion matrices, error categorizations, dataset balance checks, and empirical recommendations.
    """

    def __init__(self, min_source_samples: int = 3):
        self.min_source_samples = min_source_samples

    def analyze(
        self,
        metrics_data: Dict[str, Any],
        raw_run_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes full evaluation analysis using metric summaries and optional raw itemized results.
        """
        cm_data = metrics_data.get("confusion_matrix", {})
        clf_metrics = metrics_data.get("classification_metrics", {})
        src_breakdown = metrics_data.get("per_source_breakdown", {})
        conf_analysis = metrics_data.get("confidence_analysis", {})
        latency_data = metrics_data.get("latency_and_performance", {})
        meta_data = metrics_data.get("metadata", {})

        raw_results = raw_run_data.get("results", []) if raw_run_data else []

        # 1. Confusion Matrix (Raw & Normalized)
        tp = cm_data.get("tp", 0)
        fp = cm_data.get("fp", 0)
        tn = cm_data.get("tn", 0)
        fn = cm_data.get("fn", 0)

        actual_human_total = tn + fp
        actual_ai_total = fn + tp

        confusion_matrix = {
            "raw": {
                "true_negative": tn,
                "false_positive": fp,
                "false_negative": fn,
                "true_positive": tp
            },
            "normalized": {
                "human_actual": {
                    "predicted_human": safe_div(tn, actual_human_total),
                    "predicted_ai": safe_div(fp, actual_human_total)
                },
                "ai_actual": {
                    "predicted_human": safe_div(fn, actual_ai_total),
                    "predicted_ai": safe_div(tp, actual_ai_total)
                }
            }
        }

        # 2. Error Analysis
        fp_rate = safe_div(fp, actual_human_total)
        fn_rate = safe_div(fn, actual_ai_total)

        fp_samples = []
        fn_samples = []

        for item in raw_results:
            if not item.get("success", True):
                continue
            gt = str(item.get("ground_truth", "")).lower()
            pred = str(item.get("predicted_label", "")).lower()

            sample_summary = {
                "id": item.get("id"),
                "path": item.get("path"),
                "filename": item.get("filename"),
                "ground_truth": item.get("ground_truth"),
                "predicted_label": item.get("predicted_label"),
                "ai_probability": item.get("ai_probability"),
                "confidence": item.get("confidence"),
                "source": item.get("source")
            }

            if gt == "human" and pred == "ai":
                fp_samples.append(sample_summary)
            elif gt == "ai" and pred == "human":
                fn_samples.append(sample_summary)

        error_analysis = {
            "false_positive_rate": fp_rate,
            "false_negative_rate": fn_rate,
            "total_false_positives": len(fp_samples) if raw_results else fp,
            "total_false_negatives": len(fn_samples) if raw_results else fn,
            "false_positives": fp_samples,
            "false_negatives": fn_samples
        }

        # 3. Confidence Analysis
        correct_probs = []
        incorrect_probs = []
        fp_probs = []
        fn_probs = []

        threshold_boundary_errors = 0
        high_conf_errors = 0
        low_conf_errors = 0

        for item in raw_results:
            if not item.get("success", True):
                continue
            gt = str(item.get("ground_truth", "")).lower()
            pred = str(item.get("predicted_label", "")).lower()
            prob = item.get("ai_probability")
            conf = str(item.get("confidence", "")).lower()

            is_correct = (gt == pred)

            if prob is not None:
                if is_correct:
                    correct_probs.append(prob)
                else:
                    incorrect_probs.append(prob)
                    if 40.0 <= prob <= 60.0:
                        threshold_boundary_errors += 1
                    
                    if conf == "high" or (gt == "ai" and prob <= 25.0) or (gt == "human" and prob >= 75.0):
                        high_conf_errors += 1
                    else:
                        low_conf_errors += 1

                if gt == "human" and pred == "ai":
                    fp_probs.append(prob)
                elif gt == "ai" and pred == "human":
                    fn_probs.append(prob)

        mean_probs = conf_analysis.get("mean_probabilities", {})

        confidence_analysis_output = {
            "avg_confidence_correct": safe_mean(correct_probs, default=mean_probs.get("true_positives", 0.0)),
            "avg_confidence_incorrect": safe_mean(incorrect_probs, default=mean_probs.get("false_positives", 0.0)),
            "avg_ai_prob_false_positives": safe_mean(fp_probs, default=mean_probs.get("false_positives", 0.0)),
            "avg_ai_prob_false_negatives": safe_mean(fn_probs, default=mean_probs.get("false_negatives", 0.0)),
            "error_confidence_breakdown": {
                "threshold_boundary_errors": threshold_boundary_errors,
                "high_confidence_errors": high_conf_errors,
                "low_confidence_errors": low_conf_errors
            },
            "confidence_tiers": conf_analysis.get("confidence_tiers", {})
        }

        # 4. Dataset Balance
        human_cnt = actual_human_total
        ai_cnt = actual_ai_total
        total_eval = human_cnt + ai_cnt

        human_pct = safe_div(human_cnt * 100.0, total_eval)
        ai_pct = safe_div(ai_cnt * 100.0, total_eval)

        # Imbalanced if one class is > 65% or < 35% (when total >= 2)
        is_balanced = True
        if total_eval >= 2 and (human_pct > 65.0 or ai_pct > 65.0):
            is_balanced = False

        balance_warning = None
        if not is_balanced:
            balance_warning = (
                f"Accuracy may not represent real-world performance because the benchmark dataset is imbalanced "
                f"(Human: {human_pct}%, AI: {ai_pct}%)."
            )

        dataset_balance = {
            "human_count": human_cnt,
            "ai_count": ai_cnt,
            "total_count": total_eval,
            "human_percentage": human_pct,
            "ai_percentage": ai_pct,
            "is_balanced": is_balanced,
            "balance_status": "Balanced" if is_balanced else "Imbalanced",
            "warning": balance_warning
        }

        # 5. Source-Level Analysis
        source_analysis = {}
        for src, data in src_breakdown.items():
            s_total = data.get("total_images", 0)
            has_sufficient = s_total >= self.min_source_samples

            s_tp = data.get("tp", 0)
            s_fp = data.get("fp", 0)
            s_tn = data.get("tn", 0)
            s_fn = data.get("fn", 0)

            s_human_tot = s_tn + s_fp
            s_ai_tot = s_fn + s_tp

            s_fpr = safe_div(s_fp, s_human_tot)
            s_fnr = safe_div(s_fn, s_ai_tot)

            # Gather source AI probabilities
            src_probs = [
                item.get("ai_probability")
                for item in raw_results
                if item.get("source") == src and item.get("ai_probability") is not None
            ]
            s_avg_prob = safe_mean(src_probs, default=0.0)

            warn_msg = None
            if not has_sufficient:
                warn_msg = f"Insufficient sample size ({s_total} < {self.min_source_samples}). Metrics may not be statistically significant."

            source_analysis[src] = {
                "sample_count": s_total,
                "has_sufficient_samples": has_sufficient,
                "insufficient_sample_warning": warn_msg,
                "accuracy": data.get("accuracy", 0.0),
                "precision": data.get("precision", 0.0),
                "recall": data.get("recall", 0.0),
                "f1_score": data.get("f1_score", 0.0),
                "false_positive_rate": s_fpr,
                "false_negative_rate": s_fnr,
                "avg_ai_probability": s_avg_prob,
                "tp": s_tp,
                "fp": s_fp,
                "tn": s_tn,
                "fn": s_fn
            }

        # 6. Model-Level Analysis
        model_name = meta_data.get("model_name", "Primary Model")
        model_key = meta_data.get("model_key", "primary")

        # Extract true targets and scores for ROC-AUC
        y_true = []
        y_scores = []
        failed_count = meta_data.get("failed", 0)

        for item in raw_results:
            if not item.get("success", True):
                continue
            gt = str(item.get("ground_truth", "")).lower()
            prob = item.get("ai_probability")
            if prob is not None and gt in ["ai", "human"]:
                y_true.append(1 if gt == "ai" else 0)
                y_scores.append(prob / 100.0)

        auc_score = compute_roc_auc(y_true, y_scores)

        model_analysis = {
            "models": [
                {
                    "model_key": model_key,
                    "model_name": model_name,
                    "sample_count": total_eval,
                    "accuracy": clf_metrics.get("accuracy", 0.0),
                    "precision": clf_metrics.get("precision", 0.0),
                    "recall": clf_metrics.get("recall", 0.0),
                    "f1_score": clf_metrics.get("f1_score", 0.0),
                    "roc_auc": auc_score,
                    "false_positive_rate": fp_rate,
                    "false_negative_rate": fn_rate,
                    "avg_inference_time_ms": latency_data.get("mean_ms", 0.0),
                    "failure_rate": safe_div(failed_count, total_eval + failed_count)
                }
            ],
            "comparison_notes": [
                "Evaluated single primary forensic model." if len(meta_data) > 0 else "No multi-model execution logs found."
            ]
        }

        # 7. Error Categories
        error_categories = {
            "false_positive": {"count": fp, "sample_ids": [s["id"] for s in fp_samples if s.get("id")]},
            "false_negative": {"count": fn, "sample_ids": [s["id"] for s in fn_samples if s.get("id")]},
            "low_confidence_errors": {"count": low_conf_errors, "sample_ids": []},
            "high_confidence_errors": {"count": high_conf_errors, "sample_ids": []},
            "model_failure": {"count": failed_count, "sample_ids": []},
            "invalid_input": {"count": meta_data.get("skipped", 0), "sample_ids": []},
            "insufficient_data": {"count": 1 if total_eval < 5 else 0, "sample_ids": []}
        }

        # 8. Analysis Summary (Assessment, Strengths, Weaknesses, Warnings, Recommendations)
        strengths = []
        weaknesses = []
        warnings = []
        recommendations = []

        acc = clf_metrics.get("accuracy", 0.0)
        spec = clf_metrics.get("specificity", 0.0)
        rec = clf_metrics.get("recall", 0.0)

        if acc >= 0.90:
            strengths.append(f"High overall classification accuracy ({acc * 100:.1f}%).")
        if spec >= 0.90:
            strengths.append(f"Strong specificity ({spec * 100:.1f}%) in detecting authentic human photographs.")
        if rec >= 0.90:
            strengths.append(f"Strong sensitivity ({rec * 100:.1f}%) in identifying AI-generated media.")

        if fp_rate > 0.15:
            weaknesses.append(f"Elevated false positive rate ({fp_rate * 100:.1f}%). Authentic human images misclassified as AI.")
            recommendations.append("Human images are frequently classified as AI. Investigate false-positive cases before deployment.")

        if fn_rate > 0.15:
            weaknesses.append(f"Elevated false negative rate ({fn_rate * 100:.1f}%). AI-generated images missed by detector.")
            recommendations.append("AI-generated images are frequently missed. Investigate false-negative cases.")

        if not is_balanced:
            warnings.append(balance_warning)
            recommendations.append("Accuracy may not represent real-world performance because the benchmark dataset is imbalanced.")

        if threshold_boundary_errors > 0:
            warnings.append(f"{threshold_boundary_errors} predictions failed near the decision boundary (40%-60% AI probability).")

        if high_conf_errors > 0:
            warnings.append(f"{high_conf_errors} misclassifications occurred with high model confidence.")

        # Default fallback assessment text
        assessment_text = f"Evaluated {total_eval} images using model '{model_name}'. Accuracy: {acc * 100:.1f}%."
        if not strengths:
            strengths.append("Baseline benchmark evaluation completed.")
        if not weaknesses and fp_rate <= 0.15 and fn_rate <= 0.15:
            strengths.append("Low overall error rates across evaluated samples.")

        analysis_summary = {
            "overall_assessment": assessment_text,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "warnings": warnings,
            "recommendations": recommendations
        }

        # 9. Visualization Data (JSON structure optimized for charts)
        visualization_data = {
            "confusion_matrix": {
                "raw_matrix": [[tn, fp], [fn, tp]],
                "normalized_matrix": [
                    [safe_div(tn, actual_human_total), safe_div(fp, actual_human_total)],
                    [safe_div(fn, actual_ai_total), safe_div(tp, actual_ai_total)]
                ],
                "labels": ["Human", "AI"]
            },
            "source_comparison": [
                {
                    "source": s_name,
                    "accuracy": s_info["accuracy"],
                    "fp_rate": s_info["false_positive_rate"],
                    "fn_rate": s_info["false_negative_rate"],
                    "sample_count": s_info["sample_count"],
                    "has_sufficient_samples": s_info["has_sufficient_samples"]
                }
                for s_name, s_info in source_analysis.items()
            ],
            "model_comparison": [
                {
                    "model_name": m["model_name"],
                    "accuracy": m["accuracy"],
                    "f1_score": m["f1_score"],
                    "roc_auc": m["roc_auc"],
                    "avg_inference_time_ms": m["avg_inference_time_ms"]
                }
                for m in model_analysis["models"]
            ],
            "error_distribution": [
                {"category": cat, "count": info["count"]}
                for cat, info in error_categories.items()
            ],
            "confidence_distribution": [
                {
                    "tier": t_name,
                    "accuracy": t_info.get("accuracy", 0.0),
                    "total_count": t_info.get("total_count", 0)
                }
                for t_name, t_info in conf_analysis.get("confidence_tiers", {}).items()
            ]
        }

        return {
            "summary_metadata": {
                "run_id": meta_data.get("run_id"),
                "timestamp": meta_data.get("timestamp"),
                "model_key": model_key,
                "model_name": model_name,
                "total_evaluated": total_eval
            },
            "confusion_matrix": confusion_matrix,
            "error_analysis": error_analysis,
            "confidence_analysis": confidence_analysis_output,
            "dataset_balance": dataset_balance,
            "source_level_analysis": source_analysis,
            "model_level_analysis": model_analysis,
            "error_categories": error_categories,
            "analysis_summary": analysis_summary,
            "visualization_data": visualization_data
        }
