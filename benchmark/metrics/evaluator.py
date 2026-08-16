"""
Metrics Engine Evaluator Module
Calculates confusion matrix and evaluation metrics.
"""
import math
import numpy as np
from typing import Dict, Any, List, Optional


def compute_confusion_matrix(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Computes True Positive (TP), False Positive (FP), True Negative (TN),
    and False Negative (FN) counts from successful benchmark image predictions.
    """
    tp = 0  # Ground Truth = AI, Predicted = AI
    fp = 0  # Ground Truth = Human, Predicted = AI
    tn = 0  # Ground Truth = Human, Predicted = Human
    fn = 0  # Ground Truth = AI, Predicted = Human
    unmatched = 0

    for r in results:
        if not r.get("success", True):
            continue

        gt = str(r.get("ground_truth", "")).lower()
        pred = str(r.get("predicted_label", "")).lower()

        if gt == "ai":
            if pred == "ai":
                tp += 1
            elif pred == "human":
                fn += 1
            else:
                unmatched += 1
        elif gt == "human":
            if pred == "human":
                tn += 1
            elif pred == "ai":
                fp += 1
            else:
                unmatched += 1
        else:
            unmatched += 1

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "unmatched": unmatched,
        "total_evaluated": tp + fp + tn + fn
    }


def compute_classification_metrics(cm: Dict[str, int]) -> Dict[str, float]:
    """
    Computes Accuracy, Precision, Recall (Sensitivity), Specificity, F1-Score,
    and Balanced Accuracy from confusion matrix counts.
    """
    tp = cm.get("tp", 0)
    fp = cm.get("fp", 0)
    tn = cm.get("tn", 0)
    fn = cm.get("fn", 0)

    total = tp + fp + tn + fn

    accuracy = round((tp + tn) / total, 4) if total > 0 else 0.0
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    specificity = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0

    if (precision + recall) > 0:
        f1_score = round(2.0 * (precision * recall) / (precision + recall), 4)
    else:
        f1_score = 0.0

    balanced_accuracy = round((recall + specificity) / 2.0, 4)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1_score": f1_score,
        "balanced_accuracy": balanced_accuracy
    }


def compute_source_breakdown(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Computes accuracy, confusion matrix, and error counts per dataset source category
    (e.g., phone_camera, dslr, midjourney, dall_e, flux, etc.).
    """
    source_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        if not r.get("success", True):
            continue
        src = r.get("source", "unknown")
        source_groups.setdefault(src, []).append(r)

    breakdown: Dict[str, Dict[str, Any]] = {}
    for src, items in sorted(source_groups.items()):
        cm = compute_confusion_matrix(items)
        metrics = compute_classification_metrics(cm)
        correct = cm["tp"] + cm["tn"]
        total = cm["total_evaluated"]

        breakdown[src] = {
            "total_images": total,
            "correct_predictions": correct,
            "incorrect_predictions": total - correct,
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1_score": metrics["f1_score"],
            "tp": cm["tp"],
            "fp": cm["fp"],
            "tn": cm["tn"],
            "fn": cm["fn"]
        }

    return breakdown


def compute_confidence_analysis(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes model accuracy and average AI probabilities across confidence tiers (High, Medium, Low).
    """
    tiers: Dict[str, Dict[str, Any]] = {
        "High": {"total": 0, "correct": 0, "probs": []},
        "Medium": {"total": 0, "correct": 0, "probs": []},
        "Low": {"total": 0, "correct": 0, "probs": []},
        "Unknown": {"total": 0, "correct": 0, "probs": []}
    }

    tp_probs, fp_probs, tn_probs, fn_probs = [], [], [], []

    for r in results:
        if not r.get("success", True):
            continue

        conf_tier = r.get("confidence") or "Unknown"
        if conf_tier not in tiers:
            conf_tier = "Unknown"

        gt = str(r.get("ground_truth", "")).lower()
        pred = str(r.get("predicted_label", "")).lower()
        ai_prob = r.get("ai_probability")

        is_correct = (gt == pred)

        tiers[conf_tier]["total"] += 1
        if is_correct:
            tiers[conf_tier]["correct"] += 1

        if ai_prob is not None:
            tiers[conf_tier]["probs"].append(ai_prob)

            if gt == "ai" and pred == "ai":
                tp_probs.append(ai_prob)
            elif gt == "human" and pred == "ai":
                fp_probs.append(ai_prob)
            elif gt == "human" and pred == "human":
                tn_probs.append(ai_prob)
            elif gt == "ai" and pred == "human":
                fn_probs.append(ai_prob)

    tier_summary: Dict[str, Dict[str, Any]] = {}
    for tier, d in tiers.items():
        tot = d["total"]
        if tot > 0:
            tier_summary[tier] = {
                "total_count": tot,
                "correct_count": d["correct"],
                "accuracy": round(d["correct"] / tot, 4),
                "avg_ai_probability": round(float(np.mean(d["probs"])), 2) if d["probs"] else 0.0
            }

    def safe_mean(arr: list) -> float:
        return round(float(np.mean(arr)), 2) if arr else 0.0

    return {
        "confidence_tiers": tier_summary,
        "mean_probabilities": {
            "true_positives": safe_mean(tp_probs),
            "false_positives": safe_mean(fp_probs),
            "true_negatives": safe_mean(tn_probs),
            "false_negatives": safe_mean(fn_probs)
        }
    }


def compute_latency_metrics(results: List[Dict[str, Any]], total_duration_sec: float = 0.0) -> Dict[str, Any]:
    """
    Computes latency distribution (mean, min, max, P50, P90, P95) and throughput (images/sec).
    """
    latencies = [
        r["inference_time_ms"]
        for r in results
        if r.get("success", True) and isinstance(r.get("inference_time_ms"), (int, float))
    ]

    if not latencies:
        return {
            "evaluated_count": 0,
            "mean_ms": 0.0,
            "min_ms": 0,
            "max_ms": 0,
            "p50_ms": 0.0,
            "p90_ms": 0.0,
            "p95_ms": 0.0,
            "throughput_images_per_sec": 0.0
        }

    arr = np.array(latencies, dtype=float)
    total_imgs = len(latencies)
    throughput = round(total_imgs / total_duration_sec, 2) if total_duration_sec > 0 else 0.0

    return {
        "evaluated_count": total_imgs,
        "mean_ms": round(float(np.mean(arr)), 2),
        "min_ms": int(np.min(arr)),
        "max_ms": int(np.max(arr)),
        "p50_ms": round(float(np.percentile(arr, 50)), 2),
        "p90_ms": round(float(np.percentile(arr, 90)), 2),
        "p95_ms": round(float(np.percentile(arr, 95)), 2),
        "throughput_images_per_sec": throughput
    }


class MetricsEngine:
    """
    Primary Statistical Evaluation Engine for AI Forensic Benchmarks.
    Calculates confusion matrices, classification metrics, source breakdowns,
    confidence analyses, and latency statistics from raw benchmark run outputs.
    """

    @staticmethod
    def compute_all_metrics(run_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a full benchmark run dictionary and produces a complete metrics report.
        """
        run_summary = run_data.get("summary", {})
        results = run_data.get("results", [])

        cm = compute_confusion_matrix(results)
        clf_metrics = compute_classification_metrics(cm)
        src_breakdown = compute_source_breakdown(results)
        conf_analysis = compute_confidence_analysis(results)

        total_duration = run_summary.get("total_duration_sec", 0.0)
        latency_metrics = compute_latency_metrics(results, total_duration)

        return {
            "metadata": {
                "run_id": run_summary.get("run_id"),
                "timestamp": run_summary.get("timestamp"),
                "model_key": run_summary.get("model_key"),
                "model_name": run_summary.get("model_name"),
                "total_selected": run_summary.get("total_selected", 0),
                "successful": run_summary.get("successful", 0),
                "failed": run_summary.get("failed", 0),
                "skipped": run_summary.get("skipped", 0)
            },
            "confusion_matrix": cm,
            "classification_metrics": clf_metrics,
            "per_source_breakdown": src_breakdown,
            "confidence_analysis": conf_analysis,
            "latency_and_performance": latency_metrics
        }
