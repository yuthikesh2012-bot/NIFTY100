"""
src/run_sprint3.py

Sprint 3 orchestrator. Run with:  python -m src.run_sprint3

1. Builds the scored snapshot (latest year per company + composite_score).
2. Runs all 6 preset screeners -> output/screener_output.xlsx
3. Computes peer percentiles for all 11 peer groups -> peer_percentiles
   table in SQLite + output/peer_comparison.xlsx
4. Generates a radar chart PNG per company -> reports/radar_charts/
"""

from __future__ import annotations
import sqlite3
from pathlib import Path

from src.screener.engine import load_config, run_all_presets, build_full_snapshot
from src.reports.export_screener import export_screener_output
from src.analytics.peer import compute_peer_percentiles, write_peer_percentiles_table, unassigned_companies
from src.reports.export_peer_comparison import export_peer_comparison
from src.reports.radar_charts import generate_all_radar_charts

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "database" / "nifty100.db"
OUTPUT_DIR = REPO_ROOT / "output"
RADAR_DIR = REPO_ROOT / "reports" / "radar_charts"


def main():
    con = sqlite3.connect(DB_PATH)
    config = load_config()

    print("Building scored snapshot...")
    snapshot, full_history = build_full_snapshot(con)

    print("Running 6 preset screeners...")
    preset_results = run_all_presets(snapshot, config)
    for name, df in preset_results.items():
        print(f"  {config['presets'][name]['label']}: {len(df)} companies")

    export_screener_output(preset_results, config, OUTPUT_DIR / "screener_output.xlsx")
    print(f"Wrote {OUTPUT_DIR / 'screener_output.xlsx'}")

    print("Computing peer percentiles...")
    percentiles_df = compute_peer_percentiles(snapshot)
    n_written = write_peer_percentiles_table(con, percentiles_df)
    print(f"  peer_percentiles rows written: {n_written}")
    unassigned = unassigned_companies(snapshot)
    print(f"  {len(unassigned)} companies with No peer group assigned: {unassigned}")

    export_peer_comparison(snapshot, percentiles_df, OUTPUT_DIR / "peer_comparison.xlsx")
    print(f"Wrote {OUTPUT_DIR / 'peer_comparison.xlsx'}")

    print("Generating radar charts...")
    paths = generate_all_radar_charts(snapshot, RADAR_DIR)
    print(f"  {len(paths)} radar charts written to {RADAR_DIR}")

    con.close()
    print("Sprint 3 run complete.")


if __name__ == "__main__":
    main()
