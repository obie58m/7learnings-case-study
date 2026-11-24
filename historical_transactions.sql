SELECT DISTINCT *
FROM transactions
WHERE market = 'DE'
  AND channel = 'myshop.de'
  AND time >= TIMESTAMP '2024-09-16'
  AND time <= TIMESTAMP '2026-09-06 23:59:59'
