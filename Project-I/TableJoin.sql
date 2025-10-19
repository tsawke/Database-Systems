EXPLAIN (ANALYZE, BUFFERS)
SELECT a.prev AS src, b.curr AS dst, COUNT(*) AS paths
    FROM clickstream.events a
    JOIN clickstream.events b ON a.curr = b.prev
    GROUP BY a.prev, b.curr
    ORDER BY paths DESC
    LIMIT 20;