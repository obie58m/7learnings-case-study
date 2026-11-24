SELECT
    c.product_id,
    CAST(t.time AS DATE) AS sales_date,
    COUNT(*) AS transaction_rows,
    SUM(t.sales_before_returns) AS recorded_units
FROM historical_transactions AS t
JOIN product_attributes AS c
  ON LOWER(TRIM(t.product_id)) = LOWER(TRIM(c.product_id))
GROUP BY c.product_id, CAST(t.time AS DATE)
