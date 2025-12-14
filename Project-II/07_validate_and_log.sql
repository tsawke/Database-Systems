BEGIN;

-- 1) Foreign key integrity check (movies.country must exist in countries)
-- Expected: 0
SELECT COUNT(*) AS orphan_movie_countries
FROM movies m
LEFT JOIN countries c ON c.country_code = m.country
WHERE c.country_code IS NULL;

-- 2) tmdb_id uniqueness sanity check (should be 0 due to unique index)
SELECT COUNT(*) AS duplicated_tmdb_id_groups
FROM (
    SELECT tmdb_id
    FROM movies
    WHERE tmdb_id IS NOT NULL
    GROUP BY tmdb_id
    HAVING COUNT(*) > 1
) t;

-- 3) Basic recent coverage signal (not a hard correctness test, but useful in reports)
SELECT MAX(year_released) AS newest_year_in_movies
FROM movies;

-- 4) Log validation as a separate record (optional)
INSERT INTO movie_update_log(source, dataset_version, start_date, end_date, status, notes)
VALUES ('validate', NULL, NULL, CURRENT_DATE, 'SUCCESS', 'Validation queries executed; see outputs for counts and newest year.');

COMMIT;
