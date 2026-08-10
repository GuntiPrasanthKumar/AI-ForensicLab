import argparse
import sys
from pathlib import Path

# Add project root and ai-service to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
ai_service_dir = project_root / "ai-service"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(ai_service_dir) not in sys.path:
    sys.path.insert(0, str(ai_service_dir))

from benchmark.scripts.runner import BenchmarkRunner


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Forensic Lab - Benchmark Execution Runner"
    )
    parser.add_argument(
        "--index",
        type=str,
        default=None,
        help="Path to dataset_index.json (default: benchmark/results/dataset_index.json)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="primary",
        help="Model to benchmark ('primary', 'all', or explicit key e.g. 'hf_vit_deepfake')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for benchmark run JSON results (default: benchmark/results/)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of valid images to evaluate (e.g. --limit 20)"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Filter images by source category (e.g. --source phone_camera or --source midjourney)"
    )
    parser.add_argument(
        "--label",
        type=str,
        default=None,
        help="Filter images by ground-truth label (e.g. --label human or --label ai)"
    )
    parser.add_argument(
        "--include-duplicates",
        action="store_true",
        help="Include duplicate images in benchmark run"
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include invalid images in benchmark run"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    runner = BenchmarkRunner(
        index_path=args.index,
        output_dir=args.output_dir,
        model=args.model,
        limit=args.limit,
        source=args.source,
        label=args.label,
        include_duplicates=args.include_duplicates,
        include_invalid=args.include_invalid
    )
    runner.run()


if __name__ == "__main__":
    main()
