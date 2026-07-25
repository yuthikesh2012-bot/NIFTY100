# Sprint 3 — Screener + Peer Engine — Summary

## What's included
- `config/screener_config.yaml` — all 15 (+1 extra, see note) filterable metric definitions, 6 preset rule sets, composite-score weights — analyst-editable
- `src/screener/data_loader.py` — merges `financial_ratios` + P&L (sales/net profit) + sectors + companies + `market_cap` (P/E, P/B, div yield) into one screening DataFrame
- `src/screener/engine.py` — generic threshold filter engine + the 6 presets (D/E-skips-Financials and ICR-Debt-Free-is-infinity special cases implemented as specified)
- `src/screener/composite.py` — winsorized (P10/P90), min-max-scaled, optionally sector-relative composite quality score (35/30/20/15 weighting)
- `src/analytics/peer.py` — PERCENT_RANK-equivalent peer percentile engine for 10 metrics across 11 peer groups, with D/E inversion and graceful handling of unassigned companies
- `src/reports/export_screener.py` / `export_peer_comparison.py` — the two colour-coded Excel exports
- `src/reports/radar_charts.py` — 8-axis radar PNGs (matplotlib), peer-group or Nifty-100 overlay
- `src/run_sprint3.py` — orchestrator; `python -m src.run_sprint3` runs the whole sprint end-to-end
- `tests/dq/test_dq_rules.py` — 14 DQ rule unit tests, manually verified passing (see note below)
- Actually generated: `output/screener_output.xlsx`, `output/peer_comparison.xlsx`, `reports/radar_charts/*.png` (93 files), `peer_percentiles` table in `database/nifty100.db` (550 rows)

## Results against the Definition of Done

| Exit criterion | Result |
|---|---|
| 6 presets each return 5-50 companies | ⚠️ **4 of 6 pass**: Quality Compounder 22, Growth Accelerator 19, Dividend Champion 30, Turnaround Watch 34 ✅ — **Value Pick: 2** and **Debt-Free Blue Chip: 2** ❌ (see note) |
| `peer_comparison.xlsx` has exactly 11 sheets | ✅ Verified — `Automobiles, Consumer Finance, FMCG, IT Services, Life Insurance, Oil & Gas, Pharmaceuticals, Power & Utilities, Private Banks, Public Sector Banks, Steel` |
| Peer percentiles correct (IT Services / FMCG spot-check) | ✅ IT Services: TCS has the group's highest ROE (50.9%) and correctly gets `percentile_rank = 1.0`; lowest (TECHM) gets `0.0` |
| 14 DQ rule unit tests, 0 failures | ✅ All 14 manually verified passing (pytest not installable in this sandbox — no network access; see Sprint 2's note, same constraint) |
| Sprint review sign-off | Pending team lead demo |

### Why Value Pick and Debt-Free Blue Chip fall short of 5 companies
This is a **real finding about the current NIFTY100 universe**, not a bug — verified by hand against the underlying data:
- **Value Pick** (P/E<20, P/B<3.0, D/E<2.0, Div Yield>1%): only **9 of 93** companies even have P/B < 3 at the latest reported year — this is a quality/growth-tilted large-cap index trading at rich book multiples. Intersecting all four conditions leaves only `M&M` and `MOTHERSON`.
- **Debt-Free Blue Chip** (D/E = 0, ROE > 12%, Revenue > ₹5,000 Cr): only **3 of 93** companies are literally zero-debt at all; combined with the ROE and revenue bars, only 2 qualify.

Recommend discussing with the team lead whether to (a) accept this as a genuine screen result, (b) loosen the thresholds in `screener_config.yaml` (e.g. P/B < 4, D/E < 0.1 instead of `= 0`), or (c) widen the lookback (best-of-3-years instead of latest-year-only). No thresholds were silently changed from the sprint brief's literal spec.

### Other things worth knowing
- **ROCE proxy**: `financial_ratios` (Sprint 2) stores the ROCE *inputs* but not a `return_on_capital_employed_pct` column itself, so the composite score, peer rankings, and radar charts use **ROE as a documented fallback proxy** for the "ROCE" axis/metric everywhere it's needed. Flagging this for a Sprint 4 fix (add the real column to Sprint 2's ratio engine).
- **Year alignment**: `financial_ratios.year` is fiscal-period text (e.g. `2024-03`); `market_cap.year` is a calendar-year integer (2019-2024 only). Rows were joined on the calendar-year prefix (`2024-03` → `2024`) — a reasonable approximation, but P/E, P/B, market cap, and dividend yield are unavailable for any fiscal year before 2019 (mostly moot since presets run on latest-year data anyway).
- **Known Sprint 2 data anomalies still surface here** — e.g. `INDIGO`'s ROE shows ~893% in `screener_output.xlsx` because its source `opm_percentage`/equity figures were already flagged as anomalous in `output/ratio_edge_cases.log`. The ratio engine is computing correctly *given* that source data; the anomaly is upstream.
- **FCF Score** (radar chart axis) isn't one of the composite score's weighted sub-components as named in the brief — it's a separately winsorized/scaled version of `free_cash_flow_cr`, added just for the 8-axis radar chart since the brief lists "FCF score" as a distinct axis from the CFO/PAT-based "Cash Quality" bucket.
