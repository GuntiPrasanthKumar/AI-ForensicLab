import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from benchmark.metrics.evaluator import MetricsEngine

logging.basicConfig(
    level=logging.INFO,
    format="[ComputeMetrics] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ComputeMetrics")


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Forensic Lab - Benchmark Metrics Engine CLI"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to benchmark run JSON output (default: benchmark/results/latest_run.json)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for computed metrics JSON files (default: benchmark/results/)"
    )
    return parser.parse_args()


def process_metrics(input_path: str | Path = None, output_dir: str | Path = None) -> Dict[str, Any]:
    root = Path(__file__).resolve().parent.parent.parent
    in_file = Path(input_path).resolve() if input_path else (root / "benchmark" / "results" / "latest_run.json")
    out_dir = Path(output_dir).resolve() if output_dir else (root / "benchmark" / "results")

    if not in_file.exists():
        raise FileNotFoundError(
            f"Input benchmark run file not found at: {in_file}. "
            f"Run 'python -m benchmark.scripts.run_benchmark' first to generate a run output."
        )

    logger.info(f"Loading benchmark run data from: {in_file}")
    with open(in_file, "r", encoding="utf-8") as f:
        run_data = json.load(f)

    metrics_output = MetricsEngine.compute_all_metrics(run_data)

    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = metrics_output["metadata"].get("run_id") or "run_latest"
    
    save_file = out_dir / f"metrics_{run_id}.json"
    latest_file = out_dir / "latest_metrics.json"

    with open(save_file, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2, ensure_ascii=False)

    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2, ensure_ascii=False)

    meta = metrics_output["metadata"]
    cm = metrics_output["confusion_matrix"]
    clf = metrics_output["classification_metrics"]
    perf = metrics_output["latency_and_performance"]

    logger.info("\n======================================================")
    logger.info("Benchmark Evaluation Metrics Summary")
    logger.info("======================================================")
    logger.info(f"Run ID:             {meta.get('run_id')}")
    logger.info(f"Model Name:         {meta.get('model_name')}")
    logger.info(f"Total Evaluated:    {cm.get('total_evaluated', 0)}")
    logger.info(f"Accuracy:           {clf.get('accuracy', 0) * 100:.2f}% ({clf.get('accuracy', 0)})")
    logger.info(f"Precision:          {clf.get('precision', 0):.4f}")
    logger.info(f"Recall:             {clf.get('recall', 0):.4f}")
    logger.info(f"Specificity:        {clf.get('specificity', 0):.4f}")
    logger.info(f"F1 Score:           {clf.get('f1_score', 0):.4f}")
    logger.info(f"Balanced Accuracy:  {clf.get('balanced_accuracy', 0):.4f}")
    logger.info(f"Confusion Matrix:   TP: {cm.get('tp')} | FP: {cm.get('fp')} | TN: {cm.get('tn')} | FN: {cm.get('fn')}")
    logger.info(f"Mean Latency:       {perf.get('mean_ms', 0):.1f}ms")
    logger.info(f"P50 / P95 Latency:  {perf.get('p50_ms', 0):.1f}ms / {perf.get('p95_ms', 0):.1f}ms")
    logger.info(f"Throughput:         {perf.get('throughput_images_per_sec', 0):.2f} img/sec")
    logger.info(f"Saved Metrics:      {save_file}")
    logger.info("======================================================\n")

    return metrics_output


def main():
    args = parse_args()
    process_metrics(input_path=args.input, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
