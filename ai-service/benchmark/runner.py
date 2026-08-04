import os
import sys

# Add ai-service to python path
AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_SERVICE_DIR not in sys.path:
    sys.path.append(AI_SERVICE_DIR)

from benchmark.evaluator import BenchmarkEvaluator

def main():
    """CLI Benchmark Automation Entry Point."""
    print("\n=======================================================")
    print(" AI Forensic Lab - Automated Benchmark Laboratory Runner")
    print("=======================================================\n")
    
    evaluator = BenchmarkEvaluator()
    summary = evaluator.run_benchmark()
    
    print("\n[Runner] Benchmark execution completed successfully.")
    print(f"[Runner] Best Performing Model: {summary['best_model']['name']}")
    return summary

if __name__ == "__main__":
    main()
