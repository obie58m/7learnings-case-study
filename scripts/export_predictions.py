import csv
from datetime import date
from math import fsum, isfinite
from pathlib import Path
from tempfile import NamedTemporaryFile

import duckdb


def main():
    project = Path(__file__).resolve().parents[1]
    sql_dir = project / "sql"
    with duckdb.connect(str(project / "7ldata.duckdb"), read_only=True) as db:
        db.execute("CREATE TEMP VIEW forecast_origins AS SELECT DATE '2026-09-06' AS origin")

        for name in ("scoped_transactions", "historical_transactions", "daily_sales"):
            sql = (sql_dir / f"{name}.sql").read_text(encoding="utf-8-sig")
            db.execute(f"CREATE TEMP VIEW {name} AS {sql}")

        db.execute("CREATE TEMP VIEW forecast_history AS SELECT * FROM daily_sales")
        sql = (sql_dir / "weekday_forecasts.sql").read_text(encoding="utf-8-sig")
        db.execute(f"CREATE TEMP VIEW weekday_forecasts AS {sql}")

        model_rows = db.execute("""
            SELECT product_id, sales_date, planner_cohort, selected_forecast
            FROM weekday_forecasts
        """).fetchall()

    forecasts = {
        (product_id.strip().lower(), sales_date): (predicted_sales, planner_cohort)
        for product_id, sales_date, planner_cohort, predicted_sales in model_rows
    }
    if len(forecasts) != len(model_rows):
        raise ValueError("Duplicate product-date keys in model output.")

    rows = []
    cohort_units = []
    seen = set()
    with (project / "sample_prediction.csv").open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            product_id, date_text = row["product_id"], row["date"]
            key = (product_id.strip().lower(), date.fromisoformat(date_text))
            if key in seen:
                raise ValueError(f"Duplicate product-date key in sample: {key}")
            if key not in forecasts:
                raise ValueError(f"Missing forecast for sample key: {key}")
            seen.add(key)

            predicted_sales, planner_cohort = forecasts[key]
            if predicted_sales is None or not isfinite(predicted_sales) or predicted_sales < 0:
                raise ValueError(f"Invalid forecast for {key}: {predicted_sales}")
            rows.append((product_id, date_text, predicted_sales))
            if planner_cohort:
                cohort_units.append(predicted_sales)

    if not rows:
        raise ValueError("The sample contains no product-date rows.")

    output = project / "predictions.csv"
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=project, delete=False
    ) as target:
        temporary = Path(target.name)

    try:
        with temporary.open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target)
            writer.writerow(("product_id", "date", "predicted_sales"))
            writer.writerows(rows)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    print(f"Wrote {len(rows):,} forecasts to {output.name}.")
    print(f"Total units = {fsum(row[2] for row in rows):,.2f}")
    print(f"Focus article / Tops = {fsum(cohort_units):,.2f} units across {len(cohort_units):,} rows")


if __name__ == "__main__":
    main()
