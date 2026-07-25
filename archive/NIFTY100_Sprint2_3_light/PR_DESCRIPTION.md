Title: Consolidate sprint folders into unified project layout

Summary:
- Moved ETL modules into `src/etl/` (from Sprint1_Batch2_ETL_Core_Complete and Sprint1_Batch4_DataValidation).
- Moved config into `src/config/` (from Sprint1_Batch1_Project_Foundation).
- Moved database helpers into `src/database/` (from Sprint1_Batch5_Database).
- Moved unit tests into `tests/etl/` (from Sprint1_Batch3_UnitTests) and placed `pytest.ini` at project root.

Branch: `consolidation`
Commit: "chore: consolidate sprint files into unified src/ and tests/ structure"

How to test locally:
1. Ensure Python is available (Windows launcher or full path).
2. From the repo root run:

```
python -m pytest -q
```

Notes:
- This repo was not originally a git repository when the moves were planned; I initialized Git and committed the current snapshot. If you prefer to preserve original history from separate sprint folders, restore their original repos and perform an explicit merge.
- No remote was configured; if you want this pushed, add a remote and push the `consolidation` branch:

```
git remote add origin <url>
git push -u origin consolidation
```

Suggested PR body (copy to GitHub/GitLab):
This PR consolidates multiple Sprint folders into a single project layout to simplify development and tests.

Changes:
- ETL modules: moved to `src/etl/`
- Config: moved to `src/config/`
- Database helpers: moved to `src/database/`
- Tests: moved to `tests/etl/` and `pytest.ini` placed at repo root

All tests pass locally: `38 passed`.

Please review file moves; if you prefer a different layout (e.g., `db/` instead of `src/database/`) I can adjust and update the branch.
