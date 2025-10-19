SET search_path = clickstream, public;
EXPLAIN (ANALYZE)
SELECT curr, SUM(n) AS clicks
    FROM events
    GROUP BY curr
    ORDER BY clicks DESC
    LIMIT 20;
