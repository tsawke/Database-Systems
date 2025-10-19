CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 在 lower(curr) 上建 GIN 三元组索引（支持 ILIKE / lower(...) LIKE '%xxx%'）
CREATE INDEX IF NOT EXISTS idx_events_curr_trgm
  ON clickstream.events
  USING gin (lower(curr) gin_trgm_ops);

ANALYZE clickstream.events;