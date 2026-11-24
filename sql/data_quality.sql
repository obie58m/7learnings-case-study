WITH source_totals AS (
    SELECT COUNT(*) AS transaction_rows, SUM(sales_before_returns) AS units
    FROM scoped_transactions
), match_totals AS (
    SELECT COUNT(*) AS deduplicated_rows,
           SUM(t.sales_before_returns) AS deduplicated_units,
           COUNT(c.product_id) AS matched_rows,
           COUNT(*) FILTER (WHERE t.product_id <> c.product_id) AS normalized_matches,
           COUNT(*) FILTER (WHERE NULLIF(TRIM(t.product_id), '') IS NULL) AS missing_ids,
           COUNT(*) FILTER (
               WHERE NULLIF(TRIM(t.product_id), '') IS NOT NULL AND c.product_id IS NULL
           ) AS unmatched_ids
    FROM historical_transactions AS t
    LEFT JOIN product_attributes AS c
      ON LOWER(TRIM(t.product_id)) = LOWER(TRIM(c.product_id))
), catalog AS (
    SELECT COUNT(*) AS catalog_rows,
           COUNT(DISTINCT LOWER(NULLIF(TRIM(product_id), ''))) AS normalized_catalog_ids
    FROM product_attributes
), daily AS (
    SELECT COUNT(*) AS observed_product_days,
           COUNT(*) FILTER (WHERE recorded_units < 0) AS negative_product_days
    FROM daily_sales
)
SELECT transaction_rows,
       deduplicated_rows,
       transaction_rows - deduplicated_rows AS duplicate_rows_removed,
       units - deduplicated_units AS units_in_removed_rows,
       matched_rows, normalized_matches, missing_ids, unmatched_ids,
       catalog_rows, normalized_catalog_ids, observed_product_days, negative_product_days
FROM source_totals
CROSS JOIN match_totals
CROSS JOIN catalog
CROSS JOIN daily
