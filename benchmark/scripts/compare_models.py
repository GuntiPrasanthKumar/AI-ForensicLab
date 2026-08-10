import os
import sys
import csv
import json
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root and ai-service to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
ai_service_dir = project_root / "ai-service"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

from benchmark.scripts.runner import BenchmarkRunner
from benchmark.metrics.comparison_engine import ModelComparisonEngine
from models.model_manager import model_manager

logging.basicConfig(
    level=logging.INFO,
    format="[CompareModels] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CompareModels")


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Forensic Lab - Multi-Model Benchmark Comparison CLI"
    )
    parser.add_argument(
        "--models",
        type=str,
        default="all",
        help="Models to compare ('all' or comma-separated list e.g. 'hf_vit_deepfake,pytorch_spectral')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of valid benchmark images to evaluate per model (e.g. --limit 3)"
    )
    parser.add_argument(
        "--index", "--input",
        type=str,
        default=None,
        help="Path to dataset_index.json (default: benchmark/results/dataset_index.json)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for model comparison JSON/CSV results (default: benchmark/results/)"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Filter benchmark images by source category"
    )
    parser.add_argument(
        "--label",
        type=str,
        default=None,
        help="Filter benchmark images by ground-truth label"
    )
    return parser.parse_args()


def export_comparison_csv(comparison_data: Dict[str, Any], csv_path: Path):
    """Exports model comparison table to CSV."""
    models_dict = comparison_data.get("models", {})
    dataset_name = comparison_data.get("comparison_metadata", {}).get("dataset_id", "dataset_index.json")

    fieldnames = [
        "model", "dataset", "samples", "accuracy", "precision", "recall", "f1",
        "specificity", "false_positive_rate", "false_negative_rate", "roc_auc",
        "average_ai_probability", "average_inference_time_ms",
        "median_inference_time_ms", "failure_rate", "agreement_rate"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for m_key, m_info in models_dict.items():
            met = m_info.get("metrics", {})
            perf = m_info.get("performance", {})
            writer.writerow({
                "model": m_info.get("model_name", m_key),
                "dataset": dataset_name,
                "samples": m_info.get("samples", 0),
                "accuracy": met.get("accuracy", 0.0),
                "precision": met.get("precision", 0.0),
                "recall": met.get("recall", 0.0),
                "f1": met.get("f1_score", 0.0),
                "specificity": met.get("specificity", 0.0),
                "false_positive_rate": met.get("false_positive_rate", 0.0),
                "false_negative_rate": met.get("false_negative_rate", 0.0),
                "roc_auc": met.get("roc_auc") if met.get("roc_auc") is not None else "N/A",
                "average_ai_probability": met.get("average_ai_probability", 0.0),
                "average_inference_time_ms": perf.get("average_inference_time_ms", 0.0),
                "median_inference_time_ms": perf.get("median_inference_time_ms", 0.0),
                "failure_rate": m_info.get("failure_rate", 0.0),
                "agreement_rate": m_info.get("agreement_rate", 0.0)
            })


def process_model_comparison(
    models_setting: str = "all",
    limit: Optional[int] = None,
    index_path: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
    source: Optional[str] = None,
    label: Optional[str] = None
) -> Dict[str, Any]:
    root = Path(__file__).resolve().parent.parent.parent
    idx_file = Path(index_path).resolve() if index_path else (root / "benchmark" / "results" / "dataset_index.json")
    out_dir = Path(output_dir).resolve() if output_dir else (root / "benchmark" / "results")

    # Discover model keys to evaluate
    registered_keys = list(model_manager.registry.keys())
    target_models: List[str] = []

    if models_setting == "all" or not models_setting:
        target_models = registered_keys
    else:
        requested = [m.strip() for m in models_setting.split(",") if m.strip()]
        for req in requested:
            if req in registered_keys:
                target_models.append(req)
            else:
                logger.warning(f"Requested model '{req}' not found in ForensicModelManager registry. Discovered available: {registered_keys}")
                target_models.append(req)

    logger.info(f"Targeting Forensic Vision Models for Comparison: {target_models}")

    # Execute Benchmark Runs for each target model
    all_runs: List[Dict[str, Any]] = []

    for m_key in target_models:
        logger.info(f"\n---> Launching Benchmark Pass for Model Key: '{m_key}'")
        runner = BenchmarkRunner(
            index_path=idx_file,
            output_dir=out_dir,
            model=m_key,
            limit=limit,
            source=source,
            label=label
        )
        runs_out = runner.run()
        all_runs.extend(runs_out)

    # Read dataset bytes if available for hashing
    dataset_bytes = None
    if idx_file.exists():
        with open(idx_file, "rb") as f:
            dataset_bytes = f.read()

    # Compare runs using ModelComparisonEngine
    engine = ModelComparisonEngine()
    comp_result = engine.compare_model_runs(all_runs, dataset_name=idx_file.name, dataset_bytes=dataset_bytes)

    # Export output JSON and CSV files
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_file = out_dir / f"model_comparison_{timestamp_str}.json"
    latest_json = out_dir / "latest_model_comparison.json"
    csv_file = out_dir / f"model_comparison_{timestamp_str}.csv"
    latest_csv = out_dir / "latest_model_comparison.csv"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(comp_result, f, indent=2, ensure_ascii=False)

    with open(latest_json, "w", encoding="utf-8") as f:
        json.dump(comp_result, f, indent=2, ensure_ascii=False)

    export_comparison_csv(comp_result, csv_file)
    export_comparison_csv(comp_result, latest_csv)

    agree = comp_result.get("agreement", {})
    ranking = comp_result.get("ranking")
    models_dict = comp_result.get("models", {})

    logger.info("\n======================================================")
    logger.info("Multi-Model Comparison Summary")
    logger.info("======================================================")
    logger.info(f"Models Compared:      {len(models_dict)}")
    logger.info(f"Evaluated Images:     {agree.get('evaluated_common_images', 0)}")
    logger.info(f"Overall Agreement:    {agree.get('overall_agreement_rate', 0.0) * 100:.1f}%")
    logger.info(f"Disagreement Samples: {agree.get('disagreement_count', 0)}")

    if isinstance(ranking, list) and len(ranking) > 0:
        logger.info("\n--- Model Composite Ranking Leaderboard ---")
        for item in ranking:
            logger.info(
                f"  Rank #{item['rank']}: {item['model_name']} ({item['model_key']}) | "
                f"Composite Score: {item['composite_score']} | F1: {item['f1_score']} | "
                f"Acc: {item['accuracy']*100:.1f}% | FPR: {item['false_positive_rate']*100:.1f}% | "
                f"Latency: {item['mean_latency_ms']:.1f}ms"
            )
    else:
        logger.info("Ranking Status:       Insufficient sample data for composite model ranking (< 5 samples).")

    logger.info(f"\nSaved Comparison JSON: {json_file}")
    logger.info(f"Saved Comparison CSV:  {csv_file}")
    logger.info("======================================================\n")

    return comp_result


def main():
    args = parse_args()
    process_model_comparison(
        models_setting=args.models,
        limit=args.limit,
        index_path=args.index,
        output_dir=args.output_dir,
        source=args.source,
        label=args.label
    )


if __name__ == "__main__":
    main()
