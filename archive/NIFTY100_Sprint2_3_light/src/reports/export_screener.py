"""
src/reports/export_screener.py

Day 17 — Generates output/screener_output.xlsx: one sheet per preset (6
sheets), 20 KPI columns, sorted by composite_score descending, with
green/red conditional fills on the columns each preset actually filters on.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

REPO_ROOT = Path(__file__).resolve().parents[2]

GREEN = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
RED = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF")
BODY_FONT = Font(name="Arial", size=10)

# The 20 KPI columns shown on every preset sheet (identifier columns first).
DISPLAY_COLUMNS = [
    ("company_id", "Company"),
    ("company_name", "Company Name"),
    ("broad_sector", "Sector"),
    ("year", "Year"),
    ("return_on_equity_pct", "ROE %"),
    ("roce_proxy", "ROCE % (proxy)"),
    ("net_profit_margin_pct", "Net Profit Margin %"),
    ("operating_profit_margin_pct", "OPM %"),
    ("debt_to_equity", "D/E"),
    ("interest_coverage", "ICR"),
    ("icr_label", "ICR Label"),
    ("free_cash_flow_cr", "FCF (Cr)"),
    ("revenue_cagr_5yr", "Revenue CAGR 5yr %"),
    ("pat_cagr_5yr", "PAT CAGR 5yr %"),
    ("eps_cagr_5yr", "EPS CAGR 5yr %"),
    ("pe_ratio", "P/E"),
    ("pb_ratio", "P/B"),
    ("dividend_yield_pct", "Dividend Yield %"),
    ("market_cap_crore", "Market Cap (Cr)"),
    ("composite_score", "Composite Score"),
]

# Which display column each preset rule threshold applies to, for cell colouring.
RULE_TO_COLUMN = {
    "roe_min": "return_on_equity_pct",
    "de_max": "debt_to_equity",
    "de_equals": "debt_to_equity",
    "fcf_min": "free_cash_flow_cr",
    "fcf_positive_latest_year": "free_cash_flow_cr",
    "revenue_cagr_5yr_min": "revenue_cagr_5yr",
    "revenue_cagr_3yr_min": "revenue_cagr_5yr",  # closest available display column
    "pat_cagr_5yr_min": "pat_cagr_5yr",
    "opm_min": "operating_profit_margin_pct",
    "pe_max": "pe_ratio",
    "pb_max": "pb_ratio",
    "de_max_2": "debt_to_equity",
    "dividend_yield_min": "dividend_yield_pct",
    "dividend_payout_max": None,  # not in display columns; skipped for colouring
    "icr_min": "interest_coverage",
    "sales_min": None,
    "de_declining_yoy": "debt_to_equity",
}


def _passes_rule(row: pd.Series, rule_key: str, threshold, config: dict) -> bool | None:
    """Re-evaluate whether a single row passes a single preset rule, for cell colouring."""
    if rule_key == "de_equals":
        return row["debt_to_equity"] == threshold
    if rule_key == "dividend_payout_max":
        return row.get("dividend_payout_ratio_pct", None) is not None and \
            row["dividend_payout_ratio_pct"] <= threshold
    if rule_key == "fcf_positive_latest_year":
        return row["free_cash_flow_cr"] > 0
    if rule_key == "de_declining_yoy":
        return bool(row.get("de_declining_yoy", False))
    if rule_key.endswith("_min"):
        spec = config["filterable_metrics"].get(rule_key)
        if spec is None:
            return None
        col = "icr_effective" if spec.get("special") == "debt_free_is_infinity" else spec["column"]
        val = row.get(col)
        return None if pd.isna(val) else val >= threshold
    if rule_key.endswith("_max"):
        spec = config["filterable_metrics"].get(rule_key)
        if spec is None:
            return None
        val = row.get(spec["column"])
        if pd.isna(val):
            return None
        passes = val <= threshold
        if spec.get("special") == "skip_financials_sector" and row.get("broad_sector") == "Financials":
            return True
        return passes
    return None


def write_preset_sheet(wb: Workbook, sheet_name: str, df: pd.DataFrame, rules: dict, config: dict) -> None:
    ws = wb.create_sheet(title=sheet_name[:31])

    headers = [label for _, label in DISPLAY_COLUMNS]
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")

    rule_columns = {RULE_TO_COLUMN[k] for k in rules if RULE_TO_COLUMN.get(k)}

    for r, (_, row) in enumerate(df.iterrows(), start=2):
        for c, (col, _label) in enumerate(DISPLAY_COLUMNS, start=1):
            val = row.get(col)
            if pd.isna(val):
                val = None
            elif isinstance(val, float):
                val = round(val, 2)
            cell = ws.cell(row=r, column=c, value=val)
            cell.font = BODY_FONT

            if col in rule_columns:
                # find which rule(s) map to this column and evaluate pass/fail
                matching_rules = [k for k, v in rules.items() if RULE_TO_COLUMN.get(k) == col]
                results = [_passes_rule(row, k, v, config) for k, v in rules.items() if k in matching_rules]
                results = [r_ for r_ in results if r_ is not None]
                if results:
                    cell.fill = GREEN if all(results) else RED

    for c in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(c)].width = max(12, len(headers[c - 1]) + 2)
    ws.freeze_panes = "A2"


def export_screener_output(preset_results: dict, config: dict, out_path: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for preset_name, df in preset_results.items():
        label = config["presets"][preset_name]["label"]
        rules = config["presets"][preset_name]["rules"]
        write_preset_sheet(wb, label, df, rules, config)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
