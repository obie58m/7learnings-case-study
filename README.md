# 7Learnings retail demand forecasting case study

This submission forecasts daily unit sales before returns for **3,920 products** on `myshop.de` in Germany from **September 7–20, 2026**. The export covers all **54,880 product-date pairs** in the supplied sample and totals **230,030.50 units**.

[Forecast CSV](predictions.csv) · [Backtest results](results/baseline_evidence.txt) · [Planner evidence](results/planner_evidence.txt) · [Run instructions](#reproduce-the-results) · [Original case study](CASE_STUDY.md)

## Planner memo

- **Use 1,113 units as the working forecast for the 37 Focus article / Tops products for September 7–20.** This is about 38 units below the four-week forecast. The shorter lookback reduced pooled weighted absolute percentage error for this group from 15.56% to 14.22%.
- **Recent sales fell even on comparable days.** Sales fell 6.51%, from 1,168 to 1,092 units, when comparing the same products and weekdays. On the subset with sales and traffic in both periods, clicks fell 4.97% and units per 1,000 clicks stayed nearly flat. Lower traffic may have contributed to the decline.
- **Check voucher performance and daily availability before committing inventory.** The planned 10% voucher covers all 518 forecast product-days, up from 222 product-days on the promotion plan in the prior period. Revisit the forecast upward if comparable campaigns suggest at least 38 incremental units, or if daily stock records show shortages held back recent sales and replenishment is confirmed. The September 1 snapshot is the only stock observation.
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

Cleaned sales fell **6.53%** across all usable observations. Keeping the one negative product-day changes the decline to **5.97%**, from 1,172 to 1,102 units. Matching the same product and weekday 14 days apart gives a **6.51%** decline across 509 pairs. The decline persists under both checks.

- **Traffic.** Clicks fell while units per 1,000 clicks held steady. This pattern is consistent with a traffic-driven decline on the matched days.
- **Stock.** The only stock snapshot, on September 1, covered all 37 products and recorded zero product-days with zero starting stock. Availability on the remaining days is unknown.
- **Promotions.** Using the September 6 plan, matched sales fell 6.36% on pairs whose later day had no promotion scheduled and 6.69% on pairs whose later day had one. The forecast horizon has **518 of 518 product-days** covered by a planned 10% voucher. An overlapping 5% campaign covers 222 product-days from September 11–16. The schedule leaves voucher execution, stacking, and incremental lift uncertain. About **38 additional units**, or **3.4%** above the working forecast, would bring it back to the four-week estimate. This is a decision threshold. Estimating lift would require realized campaign data and a comparison that accounts for product and date selection. [Forecast promotion SQL](sql/planner_promotion_outlook.sql) · [Saved results](results/planner_evidence.txt)

The investigation starts with a full product-day grid for the cohort. It sums clicks and takes the minimum recorded starting stock per product-day, then flags whether any planned promotion overlaps that day. Each join preserves the product-day grain. [Cohort SQL](sql/planner_sales.sql) · [Supporting SQL](sql/planner_factors.sql) · [Saved results](results/planner_evidence.txt)

## Backtest and forecast selection

The **four-week baseline** averages a product’s observed sales for the target weekday. The **two-week comparison** uses the latest two weeks for that weekday and falls back to the four-week weekday average when needed. Both use the product’s four-week average across weekdays if the weekday average is unavailable.

The backtest forecasts days 1–14 in one pass after each origin, using sales history through that origin. The four origins were July 12, July 26, August 9, and August 23, 2026. Both methods used the same scored rows at each origin. Across the four windows, 218,314 of 219,478 overall forecasts had usable actuals. The supplied catalog labels define the cohort throughout. Historical versions of those labels are unknown.

| Validation window | Segment | Method | WAPE | MAE | RMSE | Signed bias |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Aug 24–Sep 6 | Overall | Four weeks | 22.02% | 0.877 | 1.415 | +12.29% |
| Aug 24–Sep 6 | Overall | Two weeks | 20.41% | 0.812 | 1.344 | +10.57% |
| Aug 24–Sep 6 | Overall | Export rule | 22.01% | 0.876 | 1.414 | +12.28% |
| Aug 24–Sep 6 | Focus article / Tops | Four weeks | 13.80% | 0.296 | 0.452 | +9.13% |
| Aug 24–Sep 6 | Focus article / Tops | Two weeks and export rule | 11.12% | 0.239 | 0.386 | +6.76% |
| All four windows | Overall | Four weeks | 15.09% | 0.652 | 10.743 | +3.71% |
| All four windows | Overall | Two weeks | 14.70% | 0.635 | 15.159 | +4.66% |
| All four windows | Overall | Export rule | 15.08% | 0.652 | 10.743 | +3.70% |
| All four windows | Focus article / Tops | Four weeks | 15.56% | 0.358 | 0.486 | +7.68% |
| All four windows | Focus article / Tops | Two weeks and export rule | 14.22% | 0.327 | 0.520 | +5.27% |

WAPE and signed bias divide by the sum of actual units. The script returns a missing value for either metric when that sum is zero. Positive bias means overforecasting. MAE and RMSE are in units per product-day. Pooled metrics use the individual scored rows from all four windows.

The **export rule** uses two weeks for Focus article / Tops and four weeks for the rest of the catalog. Two weeks improved cohort WAPE in three of four windows and reduced pooled overforecasting. Cohort RMSE increased from 0.486 to 0.520, so the tradeoff favors lower total absolute error and lower bias alongside some larger individual errors. Across all products, the export rule scored close to the four-week baseline. These windows informed model selection, so the scores describe retrospective performance. The working forecast assumes recent sales patterns carry forward to September 7–20. The value of an additional adjustment for broader voucher coverage remains unestimated.

A 10,000-unit observation for product `670307` on July 8 drove several large July forecast errors. Excluding that observation from training reduced pooled overall RMSE from 10.743 to 0.949 for four weeks and from 15.159 to 0.933 for two weeks. The primary run retains the observed value. [Forecast SQL](sql/weekday_forecasts.sql) · [Backtest results](results/baseline_evidence.txt) · [Sensitivity results](results/outlier_sensitivity_evidence.txt)

## Data preparation

- Kept transactions for `DE` and `myshop.de` from the start of continuous sales history on September 16, 2024 through September 6, 2026 at 23:59:59. This excludes the January 1970 timestamps. [Scope SQL](sql/scoped_transactions.sql)
- Removed 26,832 exact duplicate rows representing 100,239 recorded units. Trimming and lowercasing product IDs recovered 24,543 matches while preserving uniqueness across the 3,920 catalog IDs. The catalog join matched 2,668,586 deduplicated rows. The remaining 13,434 rows with missing IDs and 195 with unmatched IDs could not be assigned to catalog products. [Cleaning audit SQL](sql/data_quality.sql) · [Audit results](results/planner_evidence.txt)
- Summed `sales_before_returns` by product and date. Missing observations remain unknown because a missing record can indicate incomplete coverage. The model excludes 482 negative daily totals from training and scoring because the target is nonnegative sales before returns. [Daily sales SQL](sql/daily_sales.sql)

## Reproduce the results

Run the section for your operating system from the repository root. The workflow was tested on Windows with Python 3.10.7, DuckDB 1.5.6, and Zstandard 0.25.0.

### Windows (PowerShell)

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install duckdb==1.5.6 zstandard==0.25.0
```

If `7ldata.duckdb` is absent, download the archive and prepare the database.

```powershell
curl.exe --fail --location --output 7ldata.duckdb.zst "https://storage.googleapis.com/candidate-01-7l-datascience/7ldata.duckdb.zst"
if ($LASTEXITCODE -ne 0) { throw "Database download failed." }

& .\.venv\Scripts\python.exe scripts/prepare_data.py
```

```powershell
& .\.venv\Scripts\python.exe scripts/forecast_baseline.py
& .\.venv\Scripts\python.exe scripts/forecast_baseline.py --exclude-july-spike
& .\.venv\Scripts\python.exe scripts/planner_investigation.py
& .\.venv\Scripts\python.exe scripts/export_predictions.py
```

### macOS and Linux (Bash or Zsh)

Create and activate the Python environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install duckdb==1.5.6 zstandard==0.25.0
```

If `7ldata.duckdb` is absent, download and decompress the archive in the repository root.

```bash
curl --fail --location --output 7ldata.duckdb.zst \
  "https://storage.googleapis.com/candidate-01-7l-datascience/7ldata.duckdb.zst" &&
  python scripts/prepare_data.py
```

Run the backtests, planner analysis, and export.

```bash
python scripts/forecast_baseline.py
python scripts/forecast_baseline.py --exclude-july-spike
python scripts/planner_investigation.py
python scripts/export_predictions.py
```

### Generated files

The preparation script checks the decompressed size before publishing the database. The backtest and planner scripts write their evidence to `results/`. The exporter writes `predictions.csv` to the repository root and checks for missing or duplicate product-date keys and for finite, nonnegative predictions. It writes product IDs and dates in the exact order of `sample_prediction.csv`.

## AI disclosure

I used OpenAI ChatGPT and Codex to assist with Python and SQL development, debugging, code review, and documentation. I also used these tools to help review model validation results and analytical findings. I executed the code locally, checked the outputs, and reviewed the final conclusions before submission.
