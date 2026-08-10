import os
import sys
import json
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from benchmark.metrics.analysis_engine import EvaluationAnalysisEngine

logging.basicConfig(
    level=logging.INFO,
    format="[EvaluateResults] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EvaluateResults")


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Forensic Lab - Evaluation Analysis Layer CLI"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to benchmark metrics JSON input (default: benchmark/results/latest_metrics.json)"
    )
    parser.add_argument(
        "--raw-run",
        type=str,
        default=None,
        help="Path to raw benchmark run JSON input (default: benchmark/results/latest_run.json)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for evaluation analysis JSON files (default: benchmark/results/)"
    )
    parser.add_argument(
        "--min-source-samples",
        type=int,
        default=3,
        help="Minimum sample threshold for source-level statistical significance (default: 3)"
    )
    return parser.parse_args()


def process_evaluation_analysis(
    input_metrics_path: str | Path = None,
    raw_run_path: str | Path = None,
    output_dir: str | Path = None,
    min_source_samples: int = 3
) -> Dict[str, Any]:
    root = Path(__file__).resolve().parent.parent.parent
    in_metrics = Path(input_metrics_path).resolve() if input_metrics_path else (root / "benchmark" / "results" / "latest_metrics.json")
    out_dir = Path(output_dir).resolve() if output_dir else (root / "benchmark" / "results")

    if not in_metrics.exists():
        raise FileNotFoundError(
            f"Input metrics file not found at: {in_metrics}. "
            f"Run 'python -m benchmark.scripts.compute_metrics' first to generate metrics output."
        )

    logger.info(f"Loading metrics data from: {in_metrics}")
    with open(in_metrics, "r", encoding="utf-8") as f:
        metrics_data = json.load(f)

    # Resolve raw run data if available
    raw_data: Optional[Dict[str, Any]] = None
    if raw_run_path:
        r_path = Path(raw_run_path).resolve()
        if r_path.exists():
            logger.info(f"Loading raw run itemized results from: {r_path}")
            with open(r_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
    else:
        # Check default latest_run.json
        r_default = root / "benchmark" / "results" / "latest_run.json"
        if r_default.exists():
            logger.info(f"Auto-discovered raw run results from: {r_default}")
            with open(r_default, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

    engine = EvaluationAnalysisEngine(min_source_samples=min_source_samples)
    analysis_result = engine.analyze(metrics_data, raw_data)

    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    save_file = out_dir / f"evaluation_analysis_{timestamp_str}.json"
    latest_file = out_dir / "latest_evaluation_analysis.json"

    with open(save_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)

    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)

    cm_raw = analysis_result["confusion_matrix"]["raw"]
    cm_norm = analysis_result["confusion_matrix"]["normalized"]
    err = analysis_result["error_analysis"]
    bal = analysis_result["dataset_balance"]
    summary = analysis_result["analysis_summary"]

    logger.info("\n======================================================")
    logger.info("Evaluation Analysis Summary")
    logger.info("======================================================")
    logger.info(f"Raw Confusion Matrix: TN: {cm_raw['true_negative']} | FP: {cm_raw['false_positive']} | FN: {cm_raw['false_negative']} | TP: {cm_raw['true_positive']}")
    logger.info(f"Normalized (Human):   Human->Human: {cm_norm['human_actual']['predicted_human'] * 100:.1f}% | Human->AI: {cm_norm['human_actual']['predicted_ai'] * 100:.1f}%")
    logger.info(f"Normalized (AI):      AI->Human: {cm_norm['ai_actual']['predicted_human'] * 100:.1f}% | AI->AI: {cm_norm['ai_actual']['predicted_ai'] * 100:.1f}%")
    logger.info(f"False Positive Rate:  {err['false_positive_rate'] * 100:.2f}%")
    logger.info(f"False Negative Rate:  {err['false_negative_rate'] * 100:.2f}%")
    logger.info(f"Dataset Balance:      {bal['balance_status']} (Human: {bal['human_percentage']}%, AI: {bal['ai_percentage']}%)")
    logger.info(f"Recommendations:      {len(summary['recommendations'])} items")
    for r in summary["recommendations"]:
        logger.info(f"  └─ [REC] {r}")
    logger.info(f"Saved Analysis:       {save_file}")
    logger.info("======================================================\n")

    return analysis_result


def main():
    args = parse_args()
    process_evaluation_analysis(
        input_metrics_path=args.input,
        raw_run_path=args.raw_run,
        output_dir=args.output_dir,
        min_source_samples=args.min_source_samples
    )


if __name__ == "__main__":
    main()
