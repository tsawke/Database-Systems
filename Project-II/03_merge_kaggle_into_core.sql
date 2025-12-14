BEGIN;

-- A) Normalize + map country codes, and enforce FilmDB constraints deterministically in a prepared CTE
WITH prepared AS (
    SELECT
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
    FROM staging_movies_kaggle s
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
    WHERE m.title_trim100 <> ''
        AND m.year_released IS NOT NULL
        AND m.country_code IS NOT NULL
        AND EXISTS (SELECT 1 FROM countries c WHERE c.country_code = m.country_code)
),
-- B) First, attach tmdb_id to legacy rows when they match by legacy key and movies.tmdb_id is NULL
attach_tmdb AS (
    UPDATE movies m
    SET
        tmdb_id = f.tmdb_id,
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
    FROM filtered f
    WHERE m.tmdb_id IS NULL
        AND f.tmdb_id IS NOT NULL
        AND m.title = f.title_trim100
        AND m.country = f.country_code
        AND m.year_released = f.year_released
    RETURNING 1
),
-- C) Prepare rows to insert: if tmdb_id exists, insert only if no movie has same tmdb_id; if tmdb_id is NULL, insert only if no legacy-key match
to_insert_base AS (
    SELECT f.*
    FROM filtered f
    WHERE (
        f.tmdb_id IS NOT NULL 
        AND NOT EXISTS (SELECT 1 FROM movies m WHERE m.tmdb_id = f.tmdb_id)
        -- Crucial fix: Also exclude if it matches a legacy row that attach_tmdb is about to update!
        -- Because CTEs see the snapshot before update, we must manually filter these out.
        AND NOT EXISTS (
            SELECT 1 FROM movies m
            WHERE m.tmdb_id IS NULL
                AND m.title = f.title_trim100
                AND m.country = f.country_code
                AND m.year_released = f.year_released
        )
    ) OR (
        f.tmdb_id IS NULL AND NOT EXISTS (
            SELECT 1 FROM movies m
            WHERE m.title = f.title_trim100 AND m.country = f.country_code AND m.year_released = f.year_released
        )
    )
),
-- C2) Add batch-level deduplication rank
to_insert_ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY title_trim100, country_code, year_released
            ORDER BY tmdb_id
        ) as match_rn
    FROM to_insert_base
),
-- D) If a tmdb_id row collides on legacy key with a different existing tmdb_id OR with another row in the same batch, disambiguate
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
        ROW_NUMBER() OVER (ORDER BY COALESCE(ti.tmdb_id, 0), ti.title_final, ti.year_released) AS rn
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

-- E) Update existing movies by tmdb_id (primary identity) using “fill-if-null / improve-if-empty” rules
WITH prepared AS (
    SELECT
        s.tmdb_id,
        NULLIF(TRIM(s.imdb_id), '') AS imdb_id,
        SUBSTRING(TRIM(COALESCE(s.title, '')) FROM 1 FOR 100) AS title_trim100,
        TRIM(COALESCE(s.original_title, '')) AS original_title,
        NULLIF(TRIM(COALESCE(s.original_language, '')), '') AS original_language,
        s.release_date,
        CASE
            WHEN s.runtime IS NOT NULL THEN EXTRACT(YEAR FROM s.release_date)::INT
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
    FROM staging_movies_kaggle s
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
)
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
FROM filtered f
WHERE m.tmdb_id = f.tmdb_id;

-- G) Update last sync date based on actual data
-- User requested: find the latest date from the table.
-- We take MAX(release_date) but cap it at CURRENT_DATE to avoid future releases messing up the delta fetch pointer.
UPDATE pipeline_state
SET v = (
    SELECT COALESCE(MAX(release_date), '2019-12-31')::TEXT
    FROM movies
    WHERE release_date <= CURRENT_DATE
)
WHERE k = 'tmdb_last_sync';

-- F) Log run (baseline import); dataset_version is read from pipeline_state
INSERT INTO movie_update_log(source, dataset_version, start_date, end_date, status, notes)
SELECT 'kaggle', (SELECT v FROM pipeline_state WHERE k = 'kaggle_dataset_version'), NULL, CURRENT_DATE, 'SUCCESS',
             'Kaggle baseline merged. Updated tmdb_last_sync based on MAX(release_date) in db.';

COMMIT;
