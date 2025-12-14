BEGIN;

-- 1) Create a temporary table to hold the prepared and filtered staging data
--    This is necessary because we need to use this data in multiple subsequent statements (INSERT and UPDATE),
--    and a CTE is only visible to the statement it is defined in.
CREATE TEMP TABLE delta_filtered_tmp ON COMMIT DROP AS
WITH prepared AS (
  SELECT DISTINCT ON (s.tmdb_id)
    s.tmdb_id,
    NULLIF(TRIM(s.imdb_id), '') AS imdb_id,
    SUBSTRING(TRIM(COALESCE(s.title, '')) FROM 1 FOR 100) AS title_trim100,
    SUBSTRING(TRIM(COALESCE(s.original_title, '')) FROM 1 FOR 200) AS original_title,
    NULLIF(TRIM(COALESCE(s.original_language, '')), '') AS original_language,
    s.release_date,
    CASE
      WHEN s.release_date IS NOT NULL THEN EXTRACT(YEAR FROM s.release_date)::INT
      ELSE NULL
    END AS year_released,
    CASE
      WHEN s.runtime IS NULL THEN 0
      WHEN s.runtime BETWEEN 0 AND 200 THEN s.runtime
      ELSE 0
    END AS running_time_safe,
    LOWER(NULLIF(TRIM(COALESCE(s.country_iso2, '')), '')) AS country_iso2_lc,
    s.popularity,
    s.vote_average,
    s.vote_count,
    s.budget,
    s.revenue
  FROM staging_movies_tmdb_delta s
  ORDER BY s.tmdb_id
),
mapped AS (
  SELECT
    p.*,
    COALESCE(a.canonical_code, p.country_iso2_lc) AS country_code
  FROM prepared p
  LEFT JOIN country_code_alias a
    ON a.alias_code = p.country_iso2_lc
)
SELECT *
FROM mapped m
WHERE m.tmdb_id IS NOT NULL
  AND m.title_trim100 <> ''
  AND m.year_released IS NOT NULL
  AND m.country_code IS NOT NULL
  AND EXISTS (SELECT 1 FROM countries c WHERE c.country_code = m.country_code);

CREATE INDEX ON delta_filtered_tmp(tmdb_id);
CREATE INDEX ON delta_filtered_tmp(title_trim100, country_code, year_released);


-- 2) Attach to legacy rows where tmdb_id IS NULL but (Title,Country,Year) matches
--    Only attach if the tmdb_id is NOT already in use by another movie (to protect movies_tmdb_id_uq)
WITH attach_tmdb AS (
  UPDATE movies m
  SET tmdb_id = f.tmdb_id
  FROM delta_filtered_tmp f
  WHERE m.tmdb_id IS NULL
    AND m.title = f.title_trim100
    AND m.country = f.country_code
    AND m.year_released = f.year_released
    AND NOT EXISTS (SELECT 1 FROM movies m2 WHERE m2.tmdb_id = f.tmdb_id)
  RETURNING m.tmdb_id
),
-- 3) Insert new movies
--    Filter out rows that were validly attached above or already exist by tmdb_id
to_insert_base AS (
  SELECT f.*
  FROM delta_filtered_tmp f
  WHERE NOT EXISTS (SELECT 1 FROM movies m WHERE m.tmdb_id = f.tmdb_id) -- Not already in DB by ID
    AND NOT EXISTS (SELECT 1 FROM attach_tmdb a WHERE a.tmdb_id = f.tmdb_id) -- Not just attached
),
-- Add batch-level deduplication rank
to_insert_ranked AS (
  SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY title_trim100, country_code, year_released
      ORDER BY tmdb_id
    ) as match_rn
  FROM to_insert_base
),
-- Disambiguate if collision with legacy or duplicate in batch
to_insert AS (
  SELECT
    t.*,
    CASE
      -- Case 1: Collision with existing DB row (different TMDB ID)
      WHEN t.tmdb_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM movies m
        WHERE m.title = t.title_trim100 AND m.country = t.country_code AND m.year_released = t.year_released
          AND m.tmdb_id IS NOT NULL AND m.tmdb_id <> t.tmdb_id
      )
      THEN SUBSTRING(t.title_trim100 FROM 1 FOR 80) || ' [tmdb:' || t.tmdb_id::TEXT || ']'
      -- Case 2: Collision within this batch (duplicate keys in input) - match_rn > 1 means it's the 2nd/3rd instance
      WHEN t.match_rn > 1
      THEN SUBSTRING(t.title_trim100 FROM 1 FOR 80) || ' [tmdb:' || t.tmdb_id::TEXT || ']'
      ELSE t.title_trim100
    END AS title_final
  FROM to_insert_ranked t
),
numbered AS (
  SELECT
    ti.*,
    ROW_NUMBER() OVER (ORDER BY ti.tmdb_id, ti.title_final, ti.year_released) AS rn
  FROM to_insert ti
),
maxid AS (
  SELECT COALESCE(MAX(movieid), 0) AS max_movieid FROM movies
)
INSERT INTO movies (
  movieid, title, country, year_released, runtime,
  tmdb_id, imdb_id, release_date, original_title, original_language,
  popularity, vote_average, vote_count, budget, revenue
)
SELECT
  (SELECT max_movieid FROM maxid) + n.rn,
  n.title_final,
  n.country_code,
  n.year_released,
  n.running_time_safe,
  n.tmdb_id,
  n.imdb_id,
  n.release_date,
  NULLIF(n.original_title, ''),
  n.original_language,
  n.popularity,
  n.vote_average,
  n.vote_count,
  n.budget,
  n.revenue
FROM numbered n;


-- 4) Update existing movies by tmdb_id
UPDATE movies m
SET
  imdb_id = COALESCE(m.imdb_id, f.imdb_id),
  release_date = COALESCE(m.release_date, f.release_date),
  original_title = COALESCE(m.original_title, NULLIF(f.original_title, '')),
  original_language = COALESCE(m.original_language, f.original_language),
  popularity = COALESCE(m.popularity, f.popularity),
  vote_average = COALESCE(m.vote_average, f.vote_average),
  vote_count = COALESCE(m.vote_count, f.vote_count),
  budget = COALESCE(m.budget, f.budget),
  revenue = COALESCE(m.revenue, f.revenue),
  runtime = CASE WHEN m.runtime = 0 AND f.running_time_safe > 0 THEN f.running_time_safe ELSE m.runtime END
FROM delta_filtered_tmp f
WHERE m.tmdb_id = f.tmdb_id;


-- 5) Update last sync date AND Log run
UPDATE pipeline_state
SET v = CURRENT_DATE::TEXT
WHERE k = 'tmdb_last_sync';

INSERT INTO movie_update_log(source, dataset_version, start_date, end_date, status, notes)
SELECT 'tmdb', NULL, NULL, CURRENT_DATE, 'SUCCESS',
       'TMDb delta merged into core tables via staging (TEMP TABLE) + deterministic merge rules.';

COMMIT;
