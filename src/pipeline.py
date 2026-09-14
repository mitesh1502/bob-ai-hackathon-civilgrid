"""
pipeline.py
-----------
Single entry-point that runs the full GridShield data pipeline in order:
  1. generate_data.py  — creates the six raw CSVs
  2. risk_engine.py    — scores every asset, writes risk_report.csv
  3. priority_engine.py — adds cost-aware priority, writes priority_report.csv
  4. recommend.py      — adds recommendations, writes final_report.csv

Usage:
  python pipeline.py          # run everything
  python pipeline.py --skip-generate   # skip data gen if CSVs already exist
"""

import os
import sys
import subprocess
import argparse

SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SRC_DIR, "data")

STEPS = [
    ("Data Generation",     os.path.join(DATA_DIR, "generate_data.py")),
    ("Risk Scoring",        os.path.join(SRC_DIR, "scoring", "risk_engine.py")),
    ("Priority Ranking",    os.path.join(SRC_DIR, "scoring", "priority_engine.py")),
    ("Recommendations",     os.path.join(SRC_DIR, "recommendation", "recommend.py")),
]


def run_step(name: str, script: str) -> bool:
    print(f"\n{'='*60}")
    print(f"  STEP: {name}")
    print(f"  Script: {script}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, script], capture_output=False, text=True)
    if result.returncode != 0:
        print(f"\n❌  {name} FAILED (exit code {result.returncode})")
        return False
    print(f"✅  {name} complete.")
    return True


def main():
    parser = argparse.ArgumentParser(description="GridShield pipeline runner")
    parser.add_argument(
        "--skip-generate", action="store_true",
        help="Skip data generation if CSVs already exist"
    )
    args = parser.parse_args()

    print("\n╔══════════════════════════════════════════╗")
    print("║   GridShield — Full Pipeline Runner      ║")
    print("╚══════════════════════════════════════════╝\n")

    for i, (name, script) in enumerate(STEPS):
        if i == 0 and args.skip_generate:
            csv_path = os.path.join(DATA_DIR, "assets.csv")
            if os.path.exists(csv_path):
                print(f"  Skipping {name} (--skip-generate, assets.csv exists)")
                continue

        ok = run_step(name, script)
        if not ok:
            print(f"\nPipeline aborted at step: {name}")
            sys.exit(1)

    print("\n╔══════════════════════════════════════════╗")
    print("║   Pipeline complete!                     ║")
    print("║   Run:  streamlit run src/app.py         ║")
    print("╚══════════════════════════════════════════╝\n")


if __name__ == "__main__":
    main()
