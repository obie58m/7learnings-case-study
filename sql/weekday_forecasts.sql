WITH history AS (
    SELECT o.origin, s.product_id, s.sales_date, s.recorded_units
    FROM forecast_origins AS o
    JOIN forecast_history AS s
      ON s.sales_date BETWEEN o.origin - 27 AND o.origin
    WHERE s.recorded_units >= 0
), product_averages AS (
    SELECT origin, product_id, AVG(recorded_units) AS average_units
    FROM history
    GROUP BY origin, product_id
), weekday_averages AS (
    SELECT origin, product_id, DAYOFWEEK(sales_date) AS weekday,
           AVG(recorded_units) AS four_week_average,
           AVG(recorded_units) FILTER (
               WHERE sales_date >= origin - 13
           ) AS two_week_average
    FROM history
    GROUP BY origin, product_id, weekday
), forecast_dates AS (
    SELECT origin, origin + CAST(horizon AS INTEGER) AS sales_date
    FROM forecast_origins
    CROSS JOIN range(1, 15) AS days(horizon)
)
SELECT p.origin, p.product_id, d.sales_date,
       COALESCE(w.four_week_average, p.average_units) AS four_week_forecast,
       COALESCE(w.two_week_average, w.four_week_average, p.average_units)
           AS two_week_forecast
FROM product_averages AS p
JOIN forecast_dates AS d ON d.origin = p.origin
LEFT JOIN weekday_averages AS w
  ON w.origin = p.origin
 AND w.product_id = p.product_id
 AND w.weekday = DAYOFWEEK(d.sales_date)
