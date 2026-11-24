# 7Learnings retail demand forecasting case study

This submission forecasts daily unit sales before returns for **3,920 products** on `myshop.de` in Germany from **September 7–20, 2026**. The export covers all **54,880 product-date pairs** in the supplied sample and totals **230,030.50 units**.

[Forecast CSV](predictions.csv) · [Backtest results](results/baseline_evidence.txt) · [Planner evidence](results/planner_evidence.txt) · [Run instructions](#reproduce-the-results) · [Original case study](CASE_STUDY.md)

## Planner memo

- **Plan for 1,113 units across the 37 Focus article / Tops products for September 7–20.** This is about 38 units below the four-week forecast. The two-week lookback reduced pooled weighted absolute percentage error for this group from 15.56% to 14.22%.
- **Recent sales fell even on comparable days.** Sales fell 6.51%, from 1,168 to 1,092 units, when comparing the same products and weekdays. On the subset with sales and traffic in both periods, clicks fell 4.97% and units per 1,000 clicks stayed nearly flat. Lower traffic may have contributed to the decline.
- **Check daily availability and confirmed replenishment.** The only stock snapshot is from September 1. If records show widespread stockouts in the later period and replenishment is confirmed for September 7–20, revise the forecast upward.
- **Balance missed sales against excess inventory.** If the forecast drives replenishment, planning too low can lead to missed sales. Planning too high can leave excess stock and increase markdowns. This recommendation uses unit volumes and qualitative tradeoffs.

## Planner investigation

| Observation across 37 products | August 10–23 | August 24–September 6 |
| --- | ---: | ---: |
| Cleaned sales (units) | 1,179 | 1,102 |
| Usable sales observations | 514 of 518 | 513 of 518 |
| Clicks on 474 matched pairs with usable sales and positive clicks | 121,415 | 115,381 |
| Units per 1,000 clicks on those pairs | 8.76 | 8.75 |
| Product-days with stock observations | 0 | 37 |
| Product-days on the promotion plan | 0 | 222 |

Cleaned sales fell **6.53%** across all usable observations. Matching the same product and weekday 14 days apart gives a similar **6.51%** decline across 509 pairs, so the difference in observation coverage has little effect on the measured decline.

- **Traffic.** Clicks fell while units per 1,000 clicks held steady. This pattern is consistent with a traffic-driven decline on the matched days.
- **Stock.** The only stock snapshot, on September 1, covered all 37 products and recorded zero product-days with zero starting stock. Availability on the remaining days is unknown.
- **Promotions.** Using the September 6 plan, matched sales fell 6.36% on pairs whose later day had no promotion scheduled and 6.69% on pairs whose later day had one. Estimating a promotion effect would require actual execution data and a comparison that accounts for which products and dates were selected.

The investigation starts with a full product-day grid for the cohort. It sums clicks and takes the minimum recorded starting stock per product-day, then flags whether any planned promotion overlaps that day. Each join preserves the product-day grain. [Cohort SQL](sql/planner_sales.sql) · [Supporting SQL](sql/planner_factors.sql) · [Saved results](results/planner_evidence.txt)

## Backtest and forecast selection

The **four-week baseline** averages a product’s observed sales for the target weekday. The **two-week comparison** uses the latest two weeks for that weekday and falls back to the four-week weekday average when needed. Both use the product’s four-week average across weekdays if the weekday average is unavailable.

The backtest forecasts days 1–14 in one pass after each origin, using sales history through that origin. The four origins were July 12, July 26, August 9, and August 23, 2026. Both methods used the same scored rows at each origin. Across the four windows, 218,314 of 219,478 overall forecasts had usable actuals. The supplied catalog labels define the cohort throughout. Historical versions of those labels are unknown.

| Validation window | Segment | Lookback | WAPE | MAE | RMSE | Signed bias |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Aug 24–Sep 6 | Overall | Four weeks | 22.02% | 0.877 | 1.415 | +12.29% |
| Aug 24–Sep 6 | Overall | Two weeks | 20.41% | 0.812 | 1.344 | +10.57% |
| Aug 24–Sep 6 | Focus article / Tops | Four weeks | 13.80% | 0.296 | 0.452 | +9.13% |
| Aug 24–Sep 6 | Focus article / Tops | Two weeks | 11.12% | 0.239 | 0.386 | +6.76% |
| All four windows | Overall | Four weeks | 15.09% | 0.652 | 10.743 | +3.71% |
| All four windows | Overall | Two weeks | 14.70% | 0.635 | 15.159 | +4.66% |
| All four windows | Focus article / Tops | Four weeks | 15.56% | 0.358 | 0.486 | +7.68% |
| All four windows | Focus article / Tops | Two weeks | 14.22% | 0.327 | 0.520 | +5.27% |

WAPE and signed bias divide by the sum of actual units. The script returns a missing value for either metric when that sum is zero. Positive bias means overforecasting. MAE and RMSE are in units per product-day. Pooled metrics use the individual scored rows from all four windows.

The **final export** uses two weeks for Focus article / Tops, where this lookback improved WAPE in three of four windows and reduced pooled overforecasting. It uses four weeks for the rest of the catalog. Across all products, the four-week lookback had lower bias and RMSE in the primary backtest. The table reports the two lookbacks applied separately. These historical windows informed model selection, and scoring the combined rule remains follow-up work. The forecast assumes that traffic, availability, and promotion activity continue to support sales patterns similar to the recent lookback periods.

A 10,000-unit observation for product `670307` on July 8 drove several large July forecast errors. Excluding that observation from training reduced pooled overall RMSE from 10.743 to 0.949 for four weeks and from 15.159 to 0.933 for two weeks. The primary run retains the observed value. [Forecast SQL](sql/weekday_forecasts.sql) · [Backtest results](results/baseline_evidence.txt) · [Sensitivity results](results/outlier_sensitivity_evidence.txt)

## Data preparation

- Kept transactions for `DE` and `myshop.de` from the start of continuous sales history on September 16, 2024 through September 6, 2026 at 23:59:59. This excludes the January 1970 timestamps.
- Removed 26,832 exact duplicate rows representing 100,239 recorded units. Trimming and lowercasing product IDs recovered 24,543 matches while preserving uniqueness across the 3,920 catalog IDs. The catalog join matched 2,668,586 deduplicated rows.
- Summed `sales_before_returns` by product and date. Missing observations remain unknown because a missing record can indicate incomplete coverage. The model excludes 482 negative daily totals from training and scoring because the target is nonnegative sales before returns. [Transaction SQL](sql/historical_transactions.sql) · [Daily sales SQL](sql/daily_sales.sql)

## Reproduce the results

Run these commands from the repository root. The scripts were run with Python 3.10 and DuckDB 1.5.6. The PowerShell commands also install Zstandard 0.25.0 for decompression.

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install duckdb==1.5.6 zstandard==0.25.0
```

If `7ldata.duckdb` is absent, download and decompress it in the repository root. The original brief includes the `curl` and `zstd` commands. On Windows, you can use Python for decompression. [Data download instructions](CASE_STUDY.md#4-environment-setup--data-preparation)

```powershell
curl.exe --fail --location --output 7ldata.duckdb.zst "https://storage.googleapis.com/candidate-01-7l-datascience/7ldata.duckdb.zst"
if ($LASTEXITCODE -ne 0) { throw "Database download failed." }

@'
from pathlib import Path

import zstandard

partial = Path("7ldata.duckdb.part")
with open("7ldata.duckdb.zst", "rb") as source, partial.open("wb") as target:
    zstandard.ZstdDecompressor().copy_stream(source, target)
partial.rename("7ldata.duckdb")
'@ | & .\.venv\Scripts\python.exe -
```

```powershell
& .\.venv\Scripts\python.exe scripts/forecast_baseline.py
& .\.venv\Scripts\python.exe scripts/forecast_baseline.py --exclude-july-spike
& .\.venv\Scripts\python.exe scripts/planner_investigation.py
& .\.venv\Scripts\python.exe scripts/export_predictions.py
```

On macOS or Linux, follow the linked data instructions, create the environment with `python3 -m venv .venv`, and activate it with `source .venv/bin/activate`. Use `python` in place of `& .\.venv\Scripts\python.exe` in the install and run commands.

The backtest and planner scripts write their evidence to `results/`. The exporter writes `predictions.csv` to the repository root. The exporter checks for missing or duplicate product-date keys and for finite, nonnegative predictions. It writes product IDs and dates in the exact order of `sample_prediction.csv`.

## AI disclosure

I used OpenAI ChatGPT and Codex to assist with Python and SQL development, debugging, code review, and documentation. I also used these tools to help review model validation results and analytical findings. I executed the code locally, checked the outputs, and reviewed the final conclusions before submission.
