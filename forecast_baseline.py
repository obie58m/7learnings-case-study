import argparse
from pathlib import Path

import duckdb


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exclude-july-spike", action="store_true")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    with duckdb.connect(str(project / "7ldata.duckdb"), read_only=True) as db:
        db.execute("""
            CREATE TEMP VIEW forecast_origins AS
            SELECT origin
            FROM (VALUES (DATE '2026-07-12'), (DATE '2026-07-26'),
                         (DATE '2026-08-09'), (DATE '2026-08-23')) AS dates(origin)
        """)
        for name in ("historical_transactions", "daily_sales"):
            sql = (project / f"{name}.sql").read_text(encoding="utf-8-sig")
            db.execute(f"CREATE TEMP VIEW {name} AS {sql}")

        history = "SELECT * FROM daily_sales"
        if args.exclude_july_spike:
            history += """
                WHERE NOT (product_id = '670307'
                           AND sales_date = DATE '2026-07-08'
                           AND recorded_units = 10000)
            """
        db.execute(f"CREATE TEMP VIEW forecast_history AS {history}")

        forecasts = (project / "weekday_forecasts.sql").read_text(encoding="utf-8-sig")
        db.execute(f"CREATE TEMP VIEW weekday_forecasts AS {forecasts}")

        result = db.execute("""
            WITH evaluated AS (
                SELECT f.origin, f.four_week_forecast, f.two_week_forecast,
                       s.recorded_units AS actual,
                       c.item_role = 'Focus article'
                       AND c.product_category_2 = 'Tops' AS planner_cohort
                FROM weekday_forecasts AS f
                JOIN product_attributes AS c USING (product_id)
                LEFT JOIN daily_sales AS s
                  ON s.product_id = f.product_id
                 AND s.sales_date = f.sales_date
                 AND s.recorded_units >= 0
            ), segments AS (
                SELECT 'Overall' AS segment, * FROM evaluated
                UNION ALL
                SELECT 'Focus article / Tops', * FROM evaluated WHERE planner_cohort
            ), forecasts AS (
                SELECT origin, segment, actual, method, predicted
                FROM segments
                CROSS JOIN LATERAL (
                    VALUES ('4 weeks', four_week_forecast), ('2 weeks', two_week_forecast)
                ) AS methods(method, predicted)
            )
            SELECT COALESCE(CAST(origin AS VARCHAR), 'Pooled') AS forecast_origin,
                   segment, method,
                   COUNT(*) AS forecast_rows,
                   COUNT(actual) AS scored_rows,
                   ROUND(100.0 * SUM(ABS(predicted - actual))
                         / NULLIF(SUM(actual), 0), 2) AS wape_pct,
                   ROUND(AVG(ABS(predicted - actual)), 3) AS mae,
                   ROUND(SQRT(AVG(POWER(predicted - actual, 2))), 3) AS rmse,
                   ROUND(100.0 * SUM(predicted - actual)
                         / NULLIF(SUM(actual), 0), 2) AS bias_pct
            FROM forecasts
            GROUP BY GROUPING SETS ((origin, segment, method), (segment, method))
            ORDER BY forecast_origin, segment DESC, method DESC
        """)

        lines = [" | ".join(column[0] for column in result.description)]
        lines.extend(" | ".join(map(str, row)) for row in result.fetchall())

    output = "\n".join(lines) + "\n"
    evidence = "outlier_sensitivity_evidence.txt" if args.exclude_july_spike else "baseline_evidence.txt"
    (project / evidence).write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
