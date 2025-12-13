BEGIN;

TRUNCATE TABLE staging_movies_kaggle;

-- Load your normalized Kaggle CSV into staging.
-- Recommended file (produced by the normalization script): ~/workspace/LargeFiles/tmdb_kaggle_normalized.csv
-- Note: COPY reads files from the DB server filesystem. If you use psql, prefer \copy so it reads from your client machine path.
-- PostgreSQL (psql) example:
--   \copy staging_movies_kaggle(tmdb_id,imdb_id,title,original_title,original_language,release_date,runtime,country_iso2,popularity,vote_average,vote_count,budget,revenue)
--   FROM '~/workspace/LargeFiles/tmdb_kaggle_normalized.csv' WITH (FORMAT csv, HEADER true);
-- openGauss (gsql) example (server-side path required):
--   COPY staging_movies_kaggle(tmdb_id,imdb_id,title,original_title,original_language,release_date,runtime,country_iso2,popularity,vote_average,vote_count,budget,revenue)
--   FROM '/abs/path/on/server/tmdb_kaggle_normalized.csv' WITH (FORMAT csv, HEADER true);

COMMIT;
