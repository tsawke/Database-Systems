BEGIN;

TRUNCATE TABLE staging_movies_tmdb_delta;

-- Load TMDb delta normalized CSV into staging.
-- Recommended file (produced by tmdb delta fetch script): ~/workspace/LargeFiles/tmdb_delta_normalized.csv
-- PostgreSQL (psql) example:
--   \copy staging_movies_tmdb_delta(tmdb_id,imdb_id,title,original_title,original_language,release_date,runtime,country_iso2,popularity,vote_average,vote_count,budget,revenue)
--   FROM '~/workspace/LargeFiles/tmdb_delta_normalized.csv' WITH (FORMAT csv, HEADER true);
-- openGauss (gsql) example (server-side path required):
--   COPY staging_movies_tmdb_delta(tmdb_id,imdb_id,title,original_title,original_language,release_date,runtime,country_iso2,popularity,vote_average,vote_count,budget,revenue)
--   FROM '/abs/path/on/server/tmdb_delta_normalized.csv' WITH (FORMAT csv, HEADER true);

COMMIT;
