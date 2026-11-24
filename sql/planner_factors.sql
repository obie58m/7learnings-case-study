WITH traffic_by_day AS (
    SELECT LOWER(TRIM(product_id)) AS product_key,
           CAST(active_since AS DATE) AS sales_date,
           SUM(total_clicks) AS clicks
    FROM traffic
    WHERE market = 'DE'
      AND channel = 'myshop.de'
      AND active_since >= TIMESTAMP '2026-08-10'
      AND active_till <= TIMESTAMP '2026-09-06 23:59:59'
    GROUP BY 1, 2
), stock_by_day AS (
    SELECT LOWER(TRIM(product_id)) AS product_key,
           active_since AS sales_date,
           MIN(stock_start_of_day) AS starting_stock
    FROM stock
    WHERE market = 'DE'
      AND channel = 'myshop.de'
      AND active_since BETWEEN DATE '2026-08-10' AND DATE '2026-09-06'
    GROUP BY 1, 2
)
SELECT s.*, t.clicks, i.starting_stock,
       EXISTS (
           SELECT 1
           FROM promotions AS p
           WHERE p.market = 'DE'
             AND p.channel = 'myshop.de'
             AND LOWER(TRIM(p.product_id)) = LOWER(TRIM(s.product_id))
             AND p.active_since < s.sales_date + INTERVAL '1 day'
             AND p.active_till >= s.sales_date
       ) AS on_promotion_plan
FROM planner_sales AS s
LEFT JOIN traffic_by_day AS t
  ON t.product_key = LOWER(TRIM(s.product_id))
 AND t.sales_date = s.sales_date
LEFT JOIN stock_by_day AS i
  ON i.product_key = LOWER(TRIM(s.product_id))
 AND i.sales_date = s.sales_date
