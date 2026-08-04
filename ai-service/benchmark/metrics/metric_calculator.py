import time
import numpy as np
from typing import Dict, Any, List, Tuple

class MetricCalculator:
    """
    Computes research-quality classification metrics, confusion matrices, 
    and system performance statistics (time & memory usage).
    """

    @staticmethod
    def compute_all_metrics(
        predictions: List[Dict[str, Any]],
        load_time_ms: float = 0.0
    ) -> Dict[str, Any]:
        """
        Input predictions format:
        [
          {
             "filepath": str,
             "filename": str,
             "category": str,
             "ground_truth": int (0 for Human, 1 for AI),
             "predicted_prob": float (0.0 to 100.0),
             "predicted_label": int (0 for Human, 1 for AI),
             "confidence": str,
             "inference_time_ms": float
          }, ...
        ]
        """
        if not predictions:
            return MetricCalculator._empty_metrics()

        tp, fp, tn, fn = 0, 0, 0, 0
        inference_times = []
        conf_scores = []
        roc_pairs = []
        category_breakdown = {}
        misclassified = []

        for p in predictions:
            gt = p["ground_truth"]
            pred = p["predicted_label"]
            prob = p["predicted_prob"]
            cat = p["category"]

            inference_times.append(p.get("inference_time_ms", 0.0))
            conf_scores.append(prob if pred == 1 else (100.0 - prob))
            roc_pairs.append((gt, prob / 100.0))

            # Category metrics
            if cat not in category_breakdown:
                category_breakdown[cat] = {"total": 0, "correct": 0}
            category_breakdown[cat]["total"] += 1

            if gt == 1 and pred == 1:
                tp += 1
                category_breakdown[cat]["correct"] += 1
            elif gt == 0 and pred == 1:
                fp += 1
                misclassified.append({
                    "filename": p["filename"],
                    "filepath": p["filepath"],
                    "category": cat,
                    "ground_truth": "Human",
                    "predicted_label": "AI",
                    "predicted_ai_prob": round(prob, 1),
                    "confidence": p["confidence"],
                    "reason": "False Positive: Human photo flagged as AI"
                })
            elif gt == 0 and pred == 0:
                tn += 1
                category_breakdown[cat]["correct"] += 1
            elif gt == 1 and pred == 0:
                fn += 1
                misclassified.append({
                    "filename": p["filename"],
                    "filepath": p["filepath"],
                    "category": cat,
                    "ground_truth": "AI",
                    "predicted_label": "Human",
                    "predicted_ai_prob": round(prob, 1),
                    "confidence": p["confidence"],
                    "reason": "False Negative: AI image flagged as Human"
                })

        total = len(predictions)
        accuracy = (tp + tn) / total
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        roc_auc = MetricCalculator._compute_roc_auc(roc_pairs)

        # Get peak RSS memory usage
        try:
            import psutil
            mem_mb = round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
        except Exception:
            mem_mb = 0.0

        # Category accuracies
        cat_accuracy = {
            c: round((data["correct"] / data["total"]) * 100.0, 1)
            for c, data in category_breakdown.items()
        }

        return {
            "total_samples": total,
            "confusion_matrix": {
                "TP": tp,
                "FP": fp,
                "TN": tn,
                "FN": fn
            },
            "metrics": {
                "accuracy": round(accuracy * 100.0, 2),
                "precision": round(precision * 100.0, 2),
                "recall": round(recall * 100.0, 2),
                "f1_score": round(f1_score * 100.0, 2),
                "specificity": round(specificity * 100.0, 2),
                "sensitivity": round(recall * 100.0, 2),
                "false_positive_rate": round(fpr * 100.0, 2),
                "false_negative_rate": round(fnr * 100.0, 2),
                "roc_auc": round(roc_auc, 4),
                "avg_confidence": round(float(np.mean(conf_scores)), 2),
                "avg_inference_time_ms": round(float(np.mean(inference_times)), 2),
                "model_loading_time_ms": round(load_time_ms, 2),
                "memory_usage_mb": mem_mb
            },
            "category_accuracy": cat_accuracy,
            "misclassified_images": misclassified
        }

    @staticmethod
    def _compute_roc_auc(predictions: List[Tuple[int, float]]) -> float:
        if not predictions:
            return 0.5
        sorted_preds = sorted(predictions, key=lambda x: x[1], reverse=True)
        pos = sum(1 for label, _ in predictions if label == 1)
        neg = len(predictions) - pos
        if pos == 0 or neg == 0:
            return 1.0

        num_higher = 0
        for i in range(len(sorted_preds)):
            if sorted_preds[i][0] == 1:
                for j in range(i + 1, len(sorted_preds)):
                    if sorted_preds[j][0] == 0:
                        num_higher += 1

        return float(num_higher / (pos * neg))

    @staticmethod
    def _empty_metrics():
        return {
            "total_samples": 0,
            "confusion_matrix": {"TP": 0, "FP": 0, "TN": 0, "FN": 0},
            "metrics": {
                "accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0,
                "specificity": 0.0, "sensitivity": 0.0, "false_positive_rate": 0.0,
                "false_negative_rate": 0.0, "roc_auc": 0.5, "avg_confidence": 0.0,
                "avg_inference_time_ms": 0.0, "model_loading_time_ms": 0.0, "memory_usage_mb": 0.0
            },
            "category_accuracy": {},
            "misclassified_images": []
        }
