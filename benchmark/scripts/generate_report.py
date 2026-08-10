import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from benchmark.reports.report_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="[GenerateReport] %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("GenerateReport")


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Forensic Lab - Benchmark Reporting Engine CLI"
    )
    parser.add_argument(
        "--run",
        type=str,
        default=None,
        help="Path to raw benchmark run JSON (default: benchmark/results/latest_run.json)"
    )
    parser.add_argument(
        "--metrics",
        type=str,
        default=None,
        help="Path to benchmark metrics JSON (default: benchmark/results/latest_metrics.json)"
    )
    parser.add_argument(
        "--analysis",
        type=str,
        default=None,
        help="Path to evaluation analysis JSON (default: benchmark/results/latest_evaluation_analysis.json)"
    )
    parser.add_argument(
        "--output-dir", "--output",
        type=str,
        default=None,
        help="Output directory for generated reports (default: benchmark/reports/)"
    )
    return parser.parse_args()


def process_report_generation(
    run_path: Optional[str | Path] = None,
    metrics_path: Optional[str | Path] = None,
    analysis_path: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None
) -> Dict[str, Path]:
    root = Path(__file__).resolve().parent.parent.parent

    r_file = Path(run_path).resolve() if run_path else (root / "benchmark" / "results" / "latest_run.json")
    m_file = Path(metrics_path).resolve() if metrics_path else (root / "benchmark" / "results" / "latest_metrics.json")
    a_file = Path(analysis_path).resolve() if analysis_path else (root / "benchmark" / "results" / "latest_evaluation_analysis.json")
    out_dir = Path(output_dir).resolve() if output_dir else (root / "benchmark" / "reports")

    # Check for missing required files and raise helpful errors
    missing_files = []
    if not m_file.exists():
        missing_files.append(f"Metrics File: '{m_file}'")
    if not a_file.exists():
        missing_files.append(f"Analysis File: '{a_file}'")

    if missing_files:
        error_msg = (
            "Cannot generate benchmark report because required input files are missing:\n" +
            "\n".join(f"  - {f}" for f in missing_files) +
            "\n\nPlease run:\n"
            "  1. 'python -m benchmark.scripts.run_benchmark'\n"
            "  2. 'python -m benchmark.scripts.compute_metrics'\n"
            "  3. 'python -m benchmark.scripts.evaluate_results'\n"
            "before executing the report generator."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Optional raw run file check
    r_arg = r_file if r_file.exists() else None
    if not r_file.exists():
        logger.warning(f"Raw run file '{r_file}' not found. Generating report using metrics and analysis data.")

    logger.info(f"Generating benchmark reports from:")
    logger.info(f"  ├─ Metrics:  {m_file}")
    logger.info(f"  ├─ Analysis: {a_file}")
    if r_arg:
        logger.info(f"  └─ Raw Run:  {r_arg}")

    generator = ReportGenerator.load_from_files(
        run_file=r_arg,
        metrics_file=m_file,
        analysis_file=a_file
    )

    created_paths = generator.generate_all_reports(out_dir)

    logger.info("\n======================================================")
    logger.info("Benchmark Reporting Completed Successfully")
    logger.info("======================================================")
    logger.info(f"JSON Report:     {created_paths['json']}")
    logger.info(f"CSV Report:      {created_paths['csv']}")
    logger.info(f"Markdown Report: {created_paths['markdown']}")
    logger.info(f"PDF Report:      {created_paths['pdf']}")
    logger.info("======================================================\n")

    return created_paths


def main():
    args = parse_args()
    process_report_generation(
        run_path=args.run,
        metrics_path=args.metrics,
        analysis_path=args.analysis,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
