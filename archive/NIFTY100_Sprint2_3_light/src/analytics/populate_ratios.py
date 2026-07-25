"""
src/analytics/populate_ratios.py

Sprint 2 orchestrator (Day 12-13):
  1. Runs the full ratio engine for all companies across all available years.
  2. Writes/updates the `financial_ratios` table in SQLite.
  3. Writes output/capital_allocation.csv (8-pattern label per company-year).
  4. Writes output/ratio_edge_cases.log (bank ROCE/ROE carve-outs & anomalies).

Run with:  python -m src.analytics.populate_ratios
"""

from __future__ import annotations
import csv
import sqlite3
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Tuple

from src.analytics import ratios as R
from src.analytics import cagr as C
from src.analytics import cashflow_kpis as CF
from src.analytics.quality_score import composite_quality_score

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "database" / "nifty100.db"
OUTPUT_DIR = REPO_ROOT / "output"

# Reported financial-year end labels only (skip half-year/interim rows like
# '2011-09' and the running 'TTM' bucket) so CAGR windows line up on annual
# steps. Rows whose "year" ends in '-03', '-06', '-09', '-12' but represent a
# non-March fiscal year-end are still included as annual points for that
# company; this mirrors how source data is structured (one row per reported
# period).
SKIP_YEAR_LABELS = {"TTM"}

NEW_COLUMNS = [
    ("high_leverage_flag", "INTEGER"),
    ("icr_label", "TEXT"),
    ("icr_warning_flag", "INTEGER"),
    ("net_debt_cr", "REAL"),
    ("revenue_cagr_3yr", "REAL"),
    ("revenue_cagr_5yr", "REAL"),
    ("revenue_cagr_5yr_flag", "TEXT"),
    ("revenue_cagr_10yr", "REAL"),
    ("pat_cagr_3yr", "REAL"),
    ("pat_cagr_5yr", "REAL"),
    ("pat_cagr_5yr_flag", "TEXT"),
    ("pat_cagr_10yr", "REAL"),
    ("eps_cagr_3yr", "REAL"),
    ("eps_cagr_5yr", "REAL"),
    ("eps_cagr_5yr_flag", "TEXT"),
    ("eps_cagr_10yr", "REAL"),
    ("cfo_quality_score", "REAL"),
    ("cfo_quality_label", "TEXT"),
    ("capex_intensity_pct", "REAL"),
    ("capex_intensity_label", "TEXT"),
    ("fcf_conversion_rate_pct", "REAL"),
    ("composite_quality_score", "REAL"),
]


def ensure_schema(con: sqlite3.Connection) -> None:
    cur = con.cursor()
    cur.execute("PRAGMA table_info(financial_ratios)")
    existing = {row[1] for row in cur.fetchall()}
    for col, coltype in NEW_COLUMNS:
        if col not in existing:
            cur.execute(f"ALTER TABLE financial_ratios ADD COLUMN {col} {coltype}")
    con.commit()


def load_all_data(con: sqlite3.Connection):
    cur = con.cursor()

    cur.execute("SELECT id, roce_percentage, roe_percentage, book_value, face_value FROM companies")
    companies = {r[0]: {"roce_pct": r[1], "roe_pct": r[2], "book_value": r[3], "face_value": r[4]}
                 for r in cur.fetchall()}

    cur.execute("SELECT company_id, broad_sector FROM sectors")
    sector_of = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("""SELECT company_id, year, sales, expenses, operating_profit, opm_percentage,
                          other_income, interest, depreciation, profit_before_tax,
                          tax_percentage, net_profit, eps, dividend_payout
                   FROM profitandloss""")
    pnl: Dict[str, Dict[str, dict]] = {}
    for r in cur.fetchall():
        cid, year = r[0], r[1]
        pnl.setdefault(cid, {})[year] = {
            "sales": r[2], "expenses": r[3], "operating_profit": r[4], "opm_percentage": r[5],
            "other_income": r[6], "interest": r[7], "depreciation": r[8],
            "profit_before_tax": r[9], "tax_percentage": r[10], "net_profit": r[11],
            "eps": r[12], "dividend_payout": r[13],
        }

    cur.execute("""SELECT company_id, year, equity_capital, reserves, borrowings,
                          other_liabilities, total_liabilities, fixed_assets, cwip,
                          investments, other_asset, total_assets
                   FROM balancesheet""")
    bs: Dict[str, Dict[str, dict]] = {}
    for r in cur.fetchall():
        cid, year = r[0], r[1]
        bs.setdefault(cid, {})[year] = {
            "equity_capital": r[2], "reserves": r[3], "borrowings": r[4],
            "other_liabilities": r[5], "total_liabilities": r[6], "fixed_assets": r[7],
            "cwip": r[8], "investments": r[9], "other_asset": r[10], "total_assets": r[11],
        }

    cur.execute("""SELECT company_id, year, operating_activity, investing_activity,
                          financing_activity, net_cash_flow
                   FROM cashflow""")
    cf: Dict[str, Dict[str, dict]] = {}
    for r in cur.fetchall():
        cid, year = r[0], r[1]
        cf.setdefault(cid, {})[year] = {
            "operating_activity": r[2], "investing_activity": r[3],
            "financing_activity": r[4], "net_cash_flow": r[5],
        }

    return companies, sector_of, pnl, bs, cf


def _sorted_years(years) -> List[str]:
    return sorted(y for y in years if y not in SKIP_YEAR_LABELS)


def _safe(v, default=0.0):
    return default if v is None else v


def compute_sector_median_roce(companies: dict, sector_of: dict) -> Optional[float]:
    financials_roce = [companies[cid]["roce_pct"] for cid, sec in sector_of.items()
                        if sec == "Financials" and companies.get(cid, {}).get("roce_pct") is not None]
    return median(financials_roce) if financials_roce else None


def build_rows(companies, sector_of, pnl, bs, cf):
    """Returns (ratio_rows, capital_allocation_rows, edge_case_lines)."""
    ratio_rows = []
    capital_rows = []
    edge_cases = []

    financials_sector_median_roce = compute_sector_median_roce(companies, sector_of)

    missing_bs_pairs = 0
    for cid, pnl_years in pnl.items():
        sector = sector_of.get(cid)
        is_fin = (sector == "Financials")
        comp_meta = companies.get(cid, {})

        years = _sorted_years(pnl_years.keys())
        revenue_series, pat_series, eps_series = [], [], []
        # Pre-pass to build ordered series for CAGR (only years with both PnL+BS+CF present
        # are used for ratio rows, but CAGR uses whatever PnL history exists).
        for y in years:
            revenue_series.append(pnl_years[y]["sales"])
            pat_series.append(pnl_years[y]["net_profit"])
            eps_series.append(pnl_years[y]["eps"])

        growth = C.compute_growth_metrics(revenue_series, pat_series, eps_series)

        cfo_hist = []
        pat_hist = []
        for y in years:
            cf_y = cf.get(cid, {}).get(y)
            pnl_y = pnl_years.get(y)
            if (cf_y is not None and pnl_y is not None
                    and cf_y["operating_activity"] is not None and pnl_y["net_profit"] is not None):
                cfo_hist.append(cf_y["operating_activity"])
                pat_hist.append(pnl_y["net_profit"])

        for y in years:
            p = pnl_years.get(y)
            b = bs.get(cid, {}).get(y)
            c = cf.get(cid, {}).get(y)
            if p is None or b is None:
                if p is not None and b is None:
                    missing_bs_pairs += 1
                    edge_cases.append(
                        f"{cid} | {y} | MISSING_BALANCE_SHEET_YEAR | P&L row exists but no matching "
                        f"Balance Sheet row for this period; company-year excluded from financial_ratios "
                        f"| category=data source issue"
                    )
                continue  # need at minimum P&L + Balance Sheet to compute ratios

            sales = _safe(p["sales"])
            net_profit = _safe(p["net_profit"])
            operating_profit = _safe(p["operating_profit"])
            other_income = _safe(p["other_income"])
            interest = _safe(p["interest"])
            equity_capital = _safe(b["equity_capital"])
            reserves = _safe(b["reserves"])
            borrowings = _safe(b["borrowings"])
            total_assets = _safe(b["total_assets"])
            investments = _safe(b["investments"])

            prof = R.compute_profitability(
                net_profit=net_profit, sales=sales, operating_profit=operating_profit,
                reported_opm_pct=p["opm_percentage"], equity_capital=equity_capital,
                reserves=reserves, borrowings=borrowings, total_assets=total_assets,
                other_income=other_income,
            )
            if prof.operating_profit_margin_pct is not None and p["opm_percentage"] is not None:
                if not R.opm_cross_check(prof.operating_profit_margin_pct, p["opm_percentage"]):
                    edge_cases.append(
                        f"{cid} | {y} | OPM_MISMATCH | computed={prof.operating_profit_margin_pct:.2f}% "
                        f"reported={p['opm_percentage']:.2f}% | category=formula discrepancy"
                    )

            lev = R.compute_leverage_efficiency(
                borrowings=borrowings, equity_capital=equity_capital, reserves=reserves,
                operating_profit=operating_profit, other_income=other_income, interest=interest,
                investments=investments, sales=sales, total_assets=total_assets,
                is_financials_sector=is_fin,
            )

            fcf = None
            capex_pct = None
            capex_lbl = None
            fcf_conv = None
            cfo_cr = None
            if c is not None and c["operating_activity"] is not None and c["investing_activity"] is not None:
                cfo_val = _safe(c["operating_activity"])
                cfi_val = _safe(c["investing_activity"])
                cff_val = _safe(c["financing_activity"])
                cfo_cr = cfo_val
                fcf = CF.free_cash_flow(cfo_val, cfi_val)
                capex_pct = CF.capex_intensity(cfi_val, sales)
                capex_lbl = CF.capex_intensity_label(capex_pct)
                fcf_conv = CF.fcf_conversion_rate(fcf, operating_profit) if fcf is not None else None

                alloc = CF.classify_capital_allocation(
                    cfo=cfo_val, cfi=cfi_val,
                    cff=cff_val, pat=net_profit,
                )
                capital_rows.append({
                    "company_id": cid, "year": y, "cfo_sign": alloc.cfo_sign,
                    "cfi_sign": alloc.cfi_sign, "cff_sign": alloc.cff_sign,
                    "pattern_label": alloc.pattern_label,
                })

            cfo_q_score = CF.cfo_quality_score(cfo_hist, pat_hist) if cfo_hist else None
            cfo_q_label = CF.cfo_quality_label(cfo_q_score)

            # Bank ROCE / ROE carve-out cross-check vs companies.xlsx pre-computed values
            if is_fin:
                edge_cases.append(
                    f"{cid} | {y} | FINANCIALS_SECTOR_CARVEOUT | high_leverage_flag suppressed "
                    f"(structurally normal for banks/NBFCs/insurance) | category=data source issue"
                )
            src_roce = comp_meta.get("roce_pct")
            if src_roce is not None and prof.return_on_capital_employed_pct is not None:
                diff = abs(prof.return_on_capital_employed_pct - src_roce)
                if diff > 5.0:
                    edge_cases.append(
                        f"{cid} | {y} | ROCE_ANOMALY | computed={prof.return_on_capital_employed_pct:.2f}% "
                        f"source={src_roce:.2f}% diff={diff:.2f}pp | category=version difference"
                    )
            src_roe = comp_meta.get("roe_pct")
            if src_roe is not None and prof.return_on_equity_pct is not None:
                diff = abs(prof.return_on_equity_pct - src_roe)
                if diff > 5.0:
                    edge_cases.append(
                        f"{cid} | {y} | ROE_ANOMALY | computed={prof.return_on_equity_pct:.2f}% "
                        f"source={src_roe:.2f}% diff={diff:.2f}pp | category=data source issue "
                        f"(source value likely stale/mis-scaled; ratio engine value used for analytics)"
                    )

            book_value_per_share = None
            if equity_capital > 0:
                face_value = comp_meta.get("face_value")
                if face_value:
                    book_value_per_share = ((equity_capital + reserves) / equity_capital) * face_value

            cqs = composite_quality_score(
                roe_pct=prof.return_on_equity_pct, roce_pct=prof.return_on_capital_employed_pct,
                icr=lev.interest_coverage, is_debt_free=(lev.icr_label == "Debt Free"),
                cfo_quality_label_value=cfo_q_label,
            )

            ratio_rows.append({
                "company_id": cid, "year": y,
                "net_profit_margin_pct": prof.net_profit_margin_pct,
                "operating_profit_margin_pct": prof.operating_profit_margin_pct,
                "return_on_equity_pct": prof.return_on_equity_pct,
                "debt_to_equity": lev.debt_to_equity,
                "interest_coverage": lev.interest_coverage,
                "asset_turnover": lev.asset_turnover,
                "free_cash_flow_cr": fcf,
                "capex_cr": (abs(cfi_val) if (c is not None and c["investing_activity"] is not None) else None),
                "earnings_per_share": p["eps"],
                "book_value_per_share": book_value_per_share,
                "dividend_payout_ratio_pct": p["dividend_payout"],
                "total_debt_cr": borrowings,
                "cash_from_operations_cr": cfo_cr,
                "high_leverage_flag": int(lev.high_leverage_flag),
                "icr_label": lev.icr_label,
                "icr_warning_flag": int(lev.icr_warning_flag),
                "net_debt_cr": lev.net_debt,
                "revenue_cagr_3yr": growth.revenue_cagr_3yr.value,
                "revenue_cagr_5yr": growth.revenue_cagr_5yr.value,
                "revenue_cagr_5yr_flag": growth.revenue_cagr_5yr.flag,
                "revenue_cagr_10yr": growth.revenue_cagr_10yr.value,
                "pat_cagr_3yr": growth.pat_cagr_3yr.value,
                "pat_cagr_5yr": growth.pat_cagr_5yr.value,
                "pat_cagr_5yr_flag": growth.pat_cagr_5yr.flag,
                "pat_cagr_10yr": growth.pat_cagr_10yr.value,
                "eps_cagr_3yr": growth.eps_cagr_3yr.value,
                "eps_cagr_5yr": growth.eps_cagr_5yr.value,
                "eps_cagr_5yr_flag": growth.eps_cagr_5yr.flag,
                "eps_cagr_10yr": growth.eps_cagr_10yr.value,
                "cfo_quality_score": cfo_q_score,
                "cfo_quality_label": cfo_q_label,
                "capex_intensity_pct": capex_pct,
                "capex_intensity_label": capex_lbl,
                "fcf_conversion_rate_pct": fcf_conv,
                "composite_quality_score": cqs,
            })

    edge_cases.append(
        f"SUMMARY | {missing_bs_pairs} P&L company-year rows had no matching Balance Sheet row "
        f"and were excluded from financial_ratios | category=data source issue"
    )
    return ratio_rows, capital_rows, edge_cases


def write_financial_ratios(con: sqlite3.Connection, rows: List[dict]) -> int:
    cur = con.cursor()
    cur.execute("DELETE FROM financial_ratios")
    cols = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in cols)
    col_list = ", ".join(cols)
    cur.executemany(
        f"INSERT INTO financial_ratios ({col_list}) VALUES ({placeholders})",
        [tuple(r[c] for c in cols) for r in rows],
    )
    con.commit()
    cur.execute("SELECT COUNT(*) FROM financial_ratios")
    return cur.fetchone()[0]


def write_capital_allocation_csv(rows: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["company_id", "year", "cfo_sign", "cfi_sign",
                                                "cff_sign", "pattern_label"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def write_edge_case_log(lines: List[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for line in lines:
            f.write(line + "\n")


def main():
    con = sqlite3.connect(DB_PATH)
    ensure_schema(con)
    companies, sector_of, pnl, bs, cf = load_all_data(con)
    ratio_rows, capital_rows, edge_cases = build_rows(companies, sector_of, pnl, bs, cf)

    row_count = write_financial_ratios(con, ratio_rows)
    write_capital_allocation_csv(capital_rows, OUTPUT_DIR / "capital_allocation.csv")
    write_edge_case_log(edge_cases, OUTPUT_DIR / "ratio_edge_cases.log")

    print(f"financial_ratios rows written: {row_count}")
    print(f"capital_allocation.csv rows: {len(capital_rows)}")
    print(f"ratio_edge_cases.log entries: {len(edge_cases)}")
    con.close()


if __name__ == "__main__":
    main()
