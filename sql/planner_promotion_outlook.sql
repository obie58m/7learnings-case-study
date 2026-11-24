WITH cohort AS (
    SELECT product_id
    FROM product_attributes
    WHERE item_role = 'Focus article' AND product_category_2 = 'Tops'
), calendar AS (
    SELECT day::DATE AS sales_date
    FROM generate_series(DATE '2026-09-07', DATE '2026-09-20', INTERVAL '1 day') AS dates(day)
), planned_days AS (
    SELECT DISTINCT c.product_id, d.sales_date, p.promotion_name, p.voucher_rate
    FROM cohort AS c
    CROSS JOIN calendar AS d
    JOIN promotions AS p
      ON LOWER(TRIM(p.product_id)) = LOWER(TRIM(c.product_id))
     AND p.active_since < d.sales_date + INTERVAL '1 day'
     AND p.active_till >= d.sales_date
    WHERE p.market = 'DE' AND p.channel = 'myshop.de'
)
SELECT promotion_name, ROUND(100 * voucher_rate, 2) AS voucher_pct,
       MIN(sales_date) AS first_date, MAX(sales_date) AS last_date,
       COUNT(DISTINCT product_id) AS products, COUNT(*) AS planned_product_days
FROM planned_days
GROUP BY promotion_name, voucher_rate
ORDER BY planned_product_days DESC, promotion_name, voucher_pct
