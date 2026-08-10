# AI Forensic Lab — Image Forensics Benchmark Report

**Run ID:** `run_20260808_222229_hf_vit_deepfake` | **Generated:** `2026-08-10T17:23:31.487745+00:00` | **Primary Model:** `PyTorch ViT DeepFake Classifier`

---

## 1. Executive Summary

- **Dataset Size:** 3 images
- **Successful / Failed:** 3 successful, 0 failed
- **Class Breakdown:** 1 Human photographs, 2 AI-generated images
- **Overall Performance:** **33.33% Accuracy** | **0.0000 F1-Score**
- **Average Inference Speed:** 27347.7 ms / image

## 2. Dataset Summary

| Metric | Count | Proportion |
| :--- | :--- | :--- |
| Total Selected Images | 3 | 100.0% |
| Valid Images Evaluated | 3 | 100.0% |
| Skipped / Invalid | 0 | 0.0% |
| Human Photographs | 1 | 33.3% |
| AI-Generated Media | 2 | 66.7% |

## 3. Confusion Matrix

### Raw Predictions
| Ground Truth \ Predicted | Predicted Human | Predicted AI |
| :--- | :--- | :--- |
| **Actual Human** | TN = **1** | FP = **0** |
| **Actual AI** | FN = **2** | TP = **0** |

### Normalized Proportions
| Ground Truth | Predicted Human % | Predicted AI % |
| :--- | :--- | :--- |
| **Actual Human** | 100.0% | 0.0% |
| **Actual AI** | 100.0% | 0.0% |

## 4. Classification Metrics

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Accuracy** | `0.3333` (33.33%) | Overall correct classification rate |
| **Precision** | `0.0000` | Proportion of AI predictions that were truly AI |
| **Recall (Sensitivity)** | `0.0000` | Proportion of actual AI images detected |
| **Specificity** | `1.0000` | Proportion of actual Human images detected |
| **F1 Score** | `0.0000` | Harmonic mean of Precision and Recall |
| **False Positive Rate** | `0.0000` (0.00%) | Rate of authentic images misclassified as AI |
| **False Negative Rate** | `1.0000` (100.00%) | Rate of AI images missed |
| **ROC-AUC** | `0.0` | Area under ROC curve across decision thresholds |

## 5. Performance & Telemetry

- **Average Inference Time:** 27347.7 ms
- **Median Latency (P50):** 1621.0 ms
- **Min / Max Latency:** 902 ms / 79520 ms
- **Failure Rate:** 0.00%

## 6. Error Analysis

- **Total False Positives:** 0
- **Total False Negatives:** 2
- **High Confidence Misclassifications:** 0
- **Failed Pipeline Inferences:** 0

### False Negative Samples (AI -> Human)
| Sample ID | Filename | Source | AI Prob | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `img_00001` | `test_ai2.jpg` | `dall_e` | 27.6% | Medium |
| `img_00002` | `test_ai1.png` | `midjourney` | 26.1% | Medium |

## 7. Source-Level Analysis

| Source | Samples | Accuracy | Precision | Recall | F1 | FPR | FNR | Avg AI Prob | Sufficiency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `dall_e` | 1 | 0.0% | 0.00 | 0.00 | 0.00 | 0.0% | 100.0% | 27.6% | Insufficient (<3) |
| `midjourney` | 1 | 0.0% | 0.00 | 0.00 | 0.00 | 0.0% | 100.0% | 26.1% | Insufficient (<3) |
| `phone_camera` | 1 | 100.0% | 0.00 | 0.00 | 0.00 | 0.0% | 0.0% | 29.2% | Insufficient (<3) |

## 8. Model Comparison

| Model | Samples | Accuracy | Precision | Recall | F1 | ROC-AUC | FPR | FNR | Avg Latency | Failure Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PyTorch ViT DeepFake Classifier` | 3 | 33.3% | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0% | 100.0% | 27347.7 ms | 0.0% |

## 9. Evaluation Warnings

- ⚠️ **WARNING:** Accuracy may not represent real-world performance because the benchmark dataset is imbalanced (Human: 33.3333%, AI: 66.6667%).

## 10. Empirical Recommendations

- 💡 **RECOMMENDATION:** AI-generated images are frequently missed. Investigate false-negative cases.
- 💡 **RECOMMENDATION:** Accuracy may not represent real-world performance because the benchmark dataset is imbalanced.
