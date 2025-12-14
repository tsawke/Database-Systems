BEGIN;

-- 0) A small metadata table to support “one-click” daily runs
CREATE TABLE IF NOT EXISTS pipeline_state (
    k VARCHAR(64) PRIMARY KEY,
    v VARCHAR(256) NOT NULL
);

-- Initialize last sync date if not present (default: end of 2019 because FilmDB newest movies are 2019)
INSERT INTO pipeline_state (k, v)
SELECT 'tmdb_last_sync', '2019-12-31'
WHERE NOT EXISTS (SELECT 1 FROM pipeline_state WHERE k = 'tmdb_last_sync');

-- Optional: record Kaggle dataset version string externally (set by user/script if desired)
INSERT INTO pipeline_state (k, v)
SELECT 'kaggle_dataset_version', 'UNKNOWN'
WHERE NOT EXISTS (SELECT 1 FROM pipeline_state WHERE k = 'kaggle_dataset_version');

-- 1) Enhancement columns on movies (run once)
ALTER TABLE movies ADD COLUMN tmdb_id BIGINT;
ALTER TABLE movies ADD COLUMN imdb_id VARCHAR(16);
ALTER TABLE movies ADD COLUMN release_date DATE;
ALTER TABLE movies ADD COLUMN original_title VARCHAR(200);
ALTER TABLE movies ADD COLUMN original_language CHAR(2);
ALTER TABLE movies ADD COLUMN popularity NUMERIC(12, 4);
ALTER TABLE movies ADD COLUMN vote_average NUMERIC(4, 2);
ALTER TABLE movies ADD COLUMN vote_count INTEGER;
ALTER TABLE movies ADD COLUMN budget BIGINT;
ALTER TABLE movies ADD COLUMN revenue BIGINT;

-- Unique index on tmdb_id (multiple NULL values are allowed)
CREATE UNIQUE INDEX IF NOT EXISTS movies_tmdb_id_uq ON movies (tmdb_id);

-- 2) Run log table
CREATE TABLE IF NOT EXISTS movie_update_log (
    sync_id BIGSERIAL PRIMARY KEY,
    run_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(32) NOT NULL,
    dataset_version VARCHAR(128),
    start_date DATE,
    end_date DATE,
    status VARCHAR(16) NOT NULL,
    notes TEXT
);

-- 3) Country code alias table (ISO -> FilmDB internal)
CREATE TABLE IF NOT EXISTS country_code_alias (
    alias_code CHAR(2) PRIMARY KEY,
    canonical_code CHAR(2) NOT NULL REFERENCES countries(country_code)
);

-- Insert minimal aliases safely (only if canonical exists and row not already present)
INSERT INTO country_code_alias(alias_code, canonical_code)
SELECT 'es', 'sp'
WHERE EXISTS (SELECT 1 FROM countries WHERE country_code = 'sp')
    AND NOT EXISTS (SELECT 1 FROM country_code_alias WHERE alias_code = 'es');

INSERT INTO country_code_alias(alias_code, canonical_code)
SELECT 'uk', 'gb'
WHERE EXISTS (SELECT 1 FROM countries WHERE country_code = 'gb')
    AND NOT EXISTS (SELECT 1 FROM country_code_alias WHERE alias_code = 'uk');

-- 4) Staging tables (persistent for reproducibility and debugging)
CREATE TABLE IF NOT EXISTS staging_movies_kaggle (
    tmdb_id BIGINT,
    imdb_id VARCHAR(16),
    title VARCHAR(512),
    original_title VARCHAR(512),
    original_language CHAR(2),
    release_date DATE,
    runtime INTEGER,
    country_iso2 CHAR(2),
    popularity NUMERIC(12, 4),
    vote_average NUMERIC(4, 2),
    vote_count INTEGER,
    budget BIGINT,
    revenue BIGINT,
    load_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS staging_movies_kaggle_tmdb_idx ON staging_movies_kaggle (tmdb_id);

CREATE TABLE IF NOT EXISTS staging_movies_tmdb_delta (
    tmdb_id BIGINT,
    imdb_id VARCHAR(16),
    title VARCHAR(512),
    original_title VARCHAR(512),
    original_language CHAR(2),
    release_date DATE,
    runtime INTEGER,
    country_iso2 CHAR(2),
    popularity NUMERIC(12, 4),
    vote_average NUMERIC(4, 2),
    vote_count INTEGER,
    budget BIGINT,
    revenue BIGINT,
    load_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS staging_movies_tmdb_delta_tmdb_idx ON staging_movies_tmdb_delta (tmdb_id);

COMMIT;
