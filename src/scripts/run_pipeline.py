"""
run_pipeline.py
---------------
GridShield — cross-platform pipeline launcher.
Runs all four data-pipeline steps in order from src/scripts/.

Usage (from the submission root):
    python src/scripts/run_pipeline.py

Or from src/scripts/ directly:
    python run_pipeline.py

Steps executed:
    1. data/generate_data.py      → 6 raw CSVs
    2. scoring/risk_engine.py     → risk_report.csv
    3. scoring/priority_engine.py → priority_report.csv
    4. recommendation/recommend.py→ final_report.csv
"""

import os
import sys
import subprocess

# src/ is one level above this script
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STEPS = [
    ("Data Generation",  os.path.join(SRC_DIR, "data",           "generate_data.py")),
    ("Risk Scoring",     os.path.join(SRC_DIR, "scoring",        "risk_engine.py")),
    ("Priority Ranking", os.path.join(SRC_DIR, "scoring",        "priority_engine.py")),
    ("Recommendations",  os.path.join(SRC_DIR, "recommendation", "recommend.py")),
]


def main():
    print("\n+==========================================+")
    print("|   GridShield -- Full Pipeline Runner      |")
    print("+==========================================+\n")

    for name, script in STEPS:
        print(f"  >> {name}")
        result = subprocess.run([sys.executable, script], capture_output=False, text=True)
        if result.returncode != 0:
            print(f"\n[FAILED]  {name} (exit code {result.returncode})")
            sys.exit(1)
        print(f"  [OK]  {name} complete.\n")

    print("+==========================================+")
    print("|   Pipeline complete!                     |")
    print("|                                          |")
    print("|   Run:                                   |")
    print("|     python -m streamlit run src/app.py   |")
    print("|     --server.port 8502                   |")
    print("+==========================================+\n")


if __name__ == "__main__":
    main()
