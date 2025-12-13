BEGIN;

-- A) Normalize + map country codes from delta staging
WITH prepared AS (
  SELECT
    s.tmdb_id,
    NULLIF(TRIM(s.imdb_id), '') AS imdb_id,
    SUBSTRING(TRIM(COALESCE(s.title, '')) FROM 1 FOR 100) AS title_trim100,
    TRIM(COALESCE(s.original_title, '')) AS original_title,
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
),
mapped AS (
  SELECT
    p.*,
    COALESCE(a.canonical_code, p.country_iso2_lc) AS country_code
  FROM prepared p
  LEFT JOIN country_code_alias a
    ON a.alias_code = p.country_iso2_lc
),
filtered AS (
  SELECT *
  FROM mapped m
  WHERE m.tmdb_id IS NOT NULL
    AND m.title_trim100 <> ''
    AND m.year_released IS NOT NULL
    AND m.country_code IS NOT NULL
    AND EXISTS (SELECT 1 FROM countries c WHERE c.country_code = m.country_code)
),
-- B) Insert missing movies by tmdb_id, with disambiguation if legacy key collides with different tmdb_id
to_insert AS (
  SELECT
    f.*,
    CASE
      WHEN EXISTS (
        SELECT 1 FROM movies m
        WHERE m.title = f.title_trim100 AND m.country = f.country_code AND m.year_released = f.year_released
          AND m.tmdb_id IS NOT NULL AND m.tmdb_id <> f.tmdb_id
      )
      THEN SUBSTRING(f.title_trim100 FROM 1 FOR 80) || ' [tmdb:' || f.tmdb_id::TEXT || ']'
      ELSE f.title_trim100
    END AS title_final
  FROM filtered f
  WHERE NOT EXISTS (SELECT 1 FROM movies m WHERE m.tmdb_id = f.tmdb_id)
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
  movieid, title, country, year_released, running_time,
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

-- C) Update existing movies by tmdb_id (fill-if-null / improve-if-empty)
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
  running_time = CASE WHEN m.running_time = 0 AND f.running_time_safe > 0 THEN f.running_time_safe ELSE m.running_time END
FROM filtered f
WHERE m.tmdb_id = f.tmdb_id;

-- D) Update last sync date to today
UPDATE pipeline_state
SET v = CURRENT_DATE::TEXT
WHERE k = 'tmdb_last_sync';

-- E) Log run
INSERT INTO movie_update_log(source, dataset_version, start_date, end_date, status, notes)
SELECT 'tmdb', NULL, NULL, CURRENT_DATE, 'SUCCESS',
       'TMDb delta merged into core tables via staging + deterministic merge rules; tmdb_last_sync updated to CURRENT_DATE.';

COMMIT;
