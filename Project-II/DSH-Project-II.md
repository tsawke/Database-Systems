# Improve the database FilmDB and Course Materials - DSH-Project-II

## Tasks

### 1. Database Enhancement

### 2. Lecture Notes Review

### 3. Course Content Proposal

## Preface

The provided `filmdb.sql` includes directives like `PRAGMA` that are not compatible with PostgreSQL/openGauss, and the country codes in it are not strictly ISO-3166, and the most significant, it's not latest (only until 2019). Overall, this report aims to refresh the database and keep it latest.

## Environment



## 1. Database Enhancement

### 1.1 Data Sources

This project requires “as new as possible”, therefore ideally updated to the day the program runs, and extensible to run daily in the future. This report provides a union plan to solve it.

#### 1.1.1 Kaggle (Daily-updated TMDB dataset)

![image-20251213022835374](./assets/image-20251213022835374.png)

Use a daily refreshed Kaggle dataset based on TMDB as the main baseline source.

#### 1.1.2 TMDB Official API

Kaggle is updated daily, but the program must reflect “today” whenever it runs. Therefore, TMDb official API is used as an incremental “delta” source after Kaggle import.

### 1.2 Workflow

1) Download Kaggle daily snapshot (baseline).
2) Load into staging tables.
3) Merge into FilmDB core tables (movies, countries, and any new enhancement tables).
4) Read last sync timestamp from a local metadata table.
5) Use TMDb Changes API to fetch changed IDs from last sync date to today.
6) Pull details for each changed movie ID; apply inserts/updates in a controlled transaction.
7) Validate constraints and export SQL.

### 1.3 Design

####  1.3.1 Preserve the original tables, add new tables and columns

Keep existing core tables (movies, countries, people, credits, e.t.c.). Add new columns and new tables for external identifiers and richer metadata.

#### 1.3.2 New high-utility tables

Enhance `movies` with new columns (nullable):

- `tmdb_id` (unique, nullable for legacy rows)
- `imdb_id` (nullable)
- `release_date` (nullable)
- `original_title` (nullable)
- `original_language` (nullable)
- `popularity` (nullable numeric)
- `vote_average` (nullable numeric)
- `vote_count` (nullable integer)
- `budget` (nullable bigint)
- `revenue` (nullable bigint)

Add new tables:

1) `movie_update_log(sync_id, run_ts, source, dataset_version, start_date, end_date, status, notes)` to record each update run.
2) `country_code_alias(alias_code, canonical_code)` to map ISO codes into FilmDB’s internal codes (e.g., map `es` to `sp` to avoid breaking the existing countries table).
3) `staging_movies_*` tables (temporary or persistent) to allow safe bulk imports and deterministic merges.

Principles:

- Keep the original `(title, country, year_released)` uniqueness for backward compatibility if possible.
- Add `UNIQUE (tmdb_id)` where `tmdb_id IS NOT NULL` to ensure stable identity for incremental updates.
- Use `tmdb_id` as the primary identifier; if `tmdb_id` is `NULL`, fall back to the legacy uniqueness key `(title, country, year_released)` to resolve identity and prevent duplicates.

### 1.4 Compatibility Strategy for PostgreSQL and openGauss

#### 1.4.1 Approach

Produce two SQL outputs for maximum safety:

- `filmdb_pg.sql` for PostgreSQL.
- `filmdb_og.sql` for openGauss.

Even though openGauss can run in PG compatibility mode, differences still exist (e.g. notably upsert syntax).

Generating two scripts avoids unexpected failures in real environments.

#### 1.4.2 Avoid DB-specific UPSERT syntax by using staging + merge logic

Instead of relying on PostgreSQL `ON CONFLICT` or openGauss `ON DUPLICATE KEY UPDATE`, implement portable merge logic:

1) Insert Kaggle rows into staging tables without strict constraints.
2) Normalize and deduplicate in SQL queries that use `NOT EXISTS` joins.
3) Update existing rows with deterministic rules (only update if new data is non-null and different).
   This approach works consistently across PostgreSQL and openGauss with minimal dialect differences.

### 1.5 Pipeline

This pipeline is designed to be reproducible and runnable **on any day**. Kaggle provides a daily-updated TMDb baseline snapshot, and the TMDb official API is used to catch up to “today” by applying incremental changes since the last sync date.

#### 1.5.1 One-time setup

1. Configure Kaggle API:

   - Save Kaggle token to `~/.kaggle/kaggle.json`.

   - Typical permissions requirement: `chmod 600 ~/.kaggle/kaggle.json`.

   - Download the dataset snapshot with Kaggle CLI:
     - `kaggle datasets download -d alanvourch/tmdb-movies-daily-updates -p ~/workspace/LargeFiles/ --unzip`


2. Confirm baseline CSV location:
   - The extracted Kaggle CSV is already available at `~/workspace/LargeFiles/TMDB_all_movies.csv`.


3. Configure TMDB API:

   - Obtain a TMDb API credential (API Read Access Token / Bearer token).

   - Export it for the pipeline runner:

     - `export TMDB_BEARER_TOKEN="YOUR_TOKEN_HERE"`.

     - Here's my API Read Access Token, it's necessary to apply one on `https://www.themoviedb.org/settings/api`.

       ![image-20251213235027253](./assets/image-20251213235027253.png)


5. Initialize DB schema enhancement (run once):

   - Apply schema extensions (new columns on `movies`, new tables `pipeline_state`, `movie_update_log`, `country_code_alias`, and staging tables).

   - This is executed by running `01_schema_enhancement.sql`.

#### 1.5.2 Daily baseline import from Kaggle

1. Normalize Kaggle CSV to a stable staging format

   - Motivation: Kaggle datasets may change column order or naming over time, normalization produces a fixed-column CSV for deterministic loading.

   - Input: `~/workspace/LargeFiles/TMDB_all_movies.csv`

   - Output: `~/workspace/LargeFiles/tmdb_kaggle_normalized.csv`


2. Load Kaggle normalized CSV into staging

   - Truncate staging and load the normalized CSV into `staging_movies_kaggle`.

   - Use `02_load_kaggle_staging.sql` plus a `\copy` (client-side) or `COPY` (server-side) command as appropriate.


3. Merge Kaggle staging into FilmDB core tables

   - Normalize and map country codes (e.g., ISO `es` mapped to FilmDB `sp`) via `country_code_alias`.
     - Insert new movies and update existing ones with deterministic rules:
       - Use `tmdb_id` as the primary identifier when available.
       - If `tmdb_id` is `NULL`, fall back to `(title, country, year_released)` as the legacy identity key.


   - Handle legacy-key collisions deterministically (e.g., if a new row’s legacy key matches an existing movie with a different `tmdb_id`, apply a traceable title suffix within length limits).

   - This is executed by `03_merge_kaggle_into_core.sql`.


4. Log baseline completion

   - Insert a success record into `movie_update_log` with `source='kaggle'` and the dataset version string if recorded.

   - This is included in `03_merge_kaggle_into_core.sql`.

//TODO check later

#### 1.5.3 Incremental catch-up using TMDb API

1. Determine the incremental window

   - Read the last successful sync date from `pipeline_state.tmdb_last_sync`.

   - Use it as `start_date`; set `end_date` to the current date (run day).

   - This can be retrieved by running `04_read_last_sync.sql`.


2. Fetch changed movie IDs and write a TMDb delta CSV

   - Use the TMDb “Changes” endpoint to fetch changed movie IDs between `start_date` and `end_date` (chunk into <=14-day windows if needed).

   - Fetch details for each changed ID, normalize fields into a stable delta CSV.

   - Output: `~/workspace/LargeFiles/tmdb_delta_normalized.csv`.


3. Load delta CSV into staging and merge into core

   1) Load `tmdb_delta_normalized.csv` into `staging_movies_tmdb_delta` using `05_load_tmdb_delta_staging.sql`.

   1. Merge delta staging into core:

      - Insert missing movies by `tmdb_id`.

      - Update existing movies by `tmdb_id` using “fill-if-null / improve-if-empty” rules.

      - Update `pipeline_state.tmdb_last_sync` to the run day for the next one-click incremental update.

      - This is executed by `06_merge_tmdb_delta_into_core.sql`.


4. Log delta completion

   - Insert a success record into `movie_update_log` with `source='tmdb'`.

   - This is included in `06_merge_tmdb_delta_into_core.sql`.

#### 1.5.4 Data validation and integrity checks

After changes:

1) Verify referential integrity:
   - Ensure every `movies.country` exists in `countries.country_code`.


2) Verify uniqueness invariants:
   - Ensure no duplicated non-null `tmdb_id` values exist in `movies` (enforced by a unique index).


3) Verify “newest year” signal:
   - Check `MAX(year_released)` to confirm the database now extends beyond 2019.


4) Log validation results:
   - Record validation execution in `movie_update_log` for traceability.


These checks are executed by `07_validate_and_log.sql`.





## 2. Lecture Notes Review

