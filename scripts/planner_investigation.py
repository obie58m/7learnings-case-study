from pathlib import Path

import duckdb


def main():
    project = Path(__file__).resolve().parents[1]
    sql_dir = project / "sql"
    results_dir = project / "results"
    checks = {
        "Sales and coverage by period": """
            SELECT period, COUNT(DISTINCT product_id) AS products,
                   COUNT(*) AS product_days,
                   COUNT(usable_units) AS usable_days,
                   COUNT(*) FILTER (WHERE recorded_units IS NULL) AS missing_days,
                   COUNT(*) FILTER (WHERE recorded_units < 0) AS negative_days,
                   SUM(recorded_units) AS signed_units,
                   SUM(usable_units) AS cleaned_units
            FROM planner_sales
            GROUP BY period
            ORDER BY period
        """,
        "Traffic, stock, and promotion coverage": """
            SELECT period,
                   COUNT(*) AS product_days,
                   COUNT(clicks) AS traffic_days,
                   COUNT(starting_stock) AS stock_days,
                   MIN(sales_date) FILTER (WHERE starting_stock IS NOT NULL)
                       AS first_stock_date,
                   MAX(sales_date) FILTER (WHERE starting_stock IS NOT NULL)
                       AS last_stock_date,
                   COUNT(*) FILTER (WHERE starting_stock = 0) AS zero_stock_days,
                   COUNT(*) FILTER (WHERE on_promotion_plan) AS planned_promotion_days
            FROM planner_factors
            GROUP BY period
            ORDER BY period
        """,
        "Traffic and sales on matched days": """
            SELECT COUNT(*) AS matched_pairs,
                   SUM(e.clicks) AS earlier_clicks,
                   SUM(l.clicks) AS later_clicks,
                   SUM(e.usable_units) AS earlier_units,
                   SUM(l.usable_units) AS later_units,
                   ROUND(1000.0 * SUM(e.usable_units) / NULLIF(SUM(e.clicks), 0), 2)
                       AS earlier_units_per_1000_clicks,
                   ROUND(1000.0 * SUM(l.usable_units) / NULLIF(SUM(l.clicks), 0), 2)
                       AS later_units_per_1000_clicks
            FROM planner_factors AS e
            JOIN planner_factors AS l
              ON l.product_id = e.product_id
             AND l.sales_date = e.sales_date + 14
            WHERE e.usable_units IS NOT NULL AND l.usable_units IS NOT NULL
              AND e.clicks > 0 AND l.clicks > 0
        """,
        "Matched sales by later promotion plan status": """
            SELECT l.on_promotion_plan AS later_day_on_plan,
                   COUNT(*) AS matched_pairs,
                   SUM(e.usable_units) AS earlier_units,
                   SUM(l.usable_units) AS later_units,
                   ROUND(100.0 * SUM(l.usable_units - e.usable_units)
                         / NULLIF(SUM(e.usable_units), 0), 2) AS change_pct
            FROM planner_factors AS e
            JOIN planner_factors AS l
              ON l.product_id = e.product_id
             AND l.sales_date = e.sales_date + 14
            WHERE e.usable_units IS NOT NULL AND l.usable_units IS NOT NULL
            GROUP BY 1
            ORDER BY 1
        """,
        "Sales on matched product and weekday pairs": """
            SELECT COUNT(*) AS matched_pairs,
                   SUM(earlier.usable_units) AS earlier_units,
                   SUM(later.usable_units) AS later_units,
                   ROUND(100.0 * (SUM(later.usable_units) - SUM(earlier.usable_units))
                         / NULLIF(SUM(earlier.usable_units), 0), 2) AS change_pct
            FROM planner_sales AS earlier
            JOIN planner_sales AS later
              ON later.product_id = earlier.product_id
             AND later.sales_date = earlier.sales_date + 14
            WHERE earlier.usable_units IS NOT NULL
              AND later.usable_units IS NOT NULL
        """,
        "Forecast-horizon promotion plan as of September 6":
            (sql_dir / "planner_promotion_outlook.sql").read_text(encoding="utf-8-sig"),
        "Transaction and catalog cleaning audit":
            (sql_dir / "data_quality.sql").read_text(encoding="utf-8-sig"),
    }

    with duckdb.connect(str(project / "7ldata.duckdb"), read_only=True) as db:
        for name in (
            "scoped_transactions", "historical_transactions", "daily_sales",
            "planner_sales", "planner_factors",
        ):
            sql = (sql_dir / f"{name}.sql").read_text(encoding="utf-8-sig")
            db.execute(f"CREATE TEMP VIEW {name} AS {sql}")

        sections = []
        for heading, sql in checks.items():
            result = db.execute(sql)
            lines = [heading, " | ".join(column[0] for column in result.description)]
            lines.extend(" | ".join(map(str, row)) for row in result.fetchall())
            sections.append("\n".join(lines))

        for table in ("traffic", "stock", "promotions"):
            columns = db.execute(f"DESCRIBE {table}").fetchall()
            print(f"{table} columns")
            print(", ".join(f"{name} ({kind})" for name, kind, *_ in columns))

    output = "\n\n".join(sections) + "\n"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "planner_evidence.txt").write_text(output, encoding="utf-8")
    print("\n" + output, end="")


if __name__ == "__main__":
    main()
