WITH cohort AS (
    SELECT product_id
    FROM product_attributes
    WHERE item_role = 'Focus article'
      AND product_category_2 = 'Tops'
), calendar AS (
    SELECT CAST(day AS DATE) AS sales_date
    FROM generate_series(
        DATE '2026-08-10', DATE '2026-09-06', INTERVAL '1 day'
    ) AS dates(day)
)
SELECT c.product_id, d.sales_date,
       CASE WHEN d.sales_date < DATE '2026-08-24'
            THEN 'Aug 10-23' ELSE 'Aug 24-Sep 6' END AS period,
       s.recorded_units,
       CASE WHEN s.recorded_units >= 0 THEN s.recorded_units END AS usable_units
FROM cohort AS c
CROSS JOIN calendar AS d
LEFT JOIN daily_sales AS s
  ON s.product_id = c.product_id
 AND s.sales_date = d.sales_date
