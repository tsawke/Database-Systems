#!/bin/bash
set -e

# daily_update_og.sh: Run Daily Update (Kaggle + TMDB Delta) for FilmDB on openGauss
# Usage: ./daily_update_og.sh
# Reference: Project II Section 1.5 Pipeline

echo "=== Starting Daily Update for FilmDB (openGauss) ==="

# 0. Environment Checks
if [ -z "$TMDB_BEARER_TOKEN" ]; then
  echo "Error: TMDB_BEARER_TOKEN is not set. Please export it."
  echo "Example: export TMDB_BEARER_TOKEN='your_token_here'"
  exit 1
fi

KAGGLE_CSV="$HOME/workspace/LargeFiles/TMDB_all_movies.csv"
KAGGLE_NORM_CSV="$HOME/workspace/LargeFiles/tmdb_kaggle_normalized.csv"
TMDB_DELTA_CSV="$HOME/workspace/LargeFiles/tmdb_delta_normalized.csv"

# 1. Daily Baseline Import from Kaggle (if available)
echo "--- [1/2] Kaggle Baseline Import ---"
if [ -f "$KAGGLE_CSV" ]; then
    echo "Found Kaggle CSV at $KAGGLE_CSV. Proceeding with normalization..."
    
    # 1.1 Normalize
    # Export country map for name-to-code resolution
    echo "Exporting country map..."
    docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -c \"COPY (SELECT country_name, country_code FROM countries) TO STDOUT WITH (FORMAT csv)\"'" > country_map.csv
    
    python3 normalize_kaggle_tmdb_csv.py \
      --in "$KAGGLE_CSV" \
      --out "$KAGGLE_NORM_CSV" \
      --chunksize 10000 \
      --country-map "country_map.csv"
      
    # 1.2 Load Staging
    echo "Loading Kaggle staging..."
    # Execute the TRUNCATE/CREATE form
    docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -1'" < 02_load_kaggle_staging.sql
    
    # Perform the data load via COPY FROM STDIN
    # Note: openGauss gsql support COPY ... FROM STDIN
    # Perform the data load via COPY FROM FILE (more robust than STDIN pipe)
    # Perform the data load via COPY FROM FILE (using SQL file to avoid quoting hell)
    echo "Copying data..."
    docker cp "$KAGGLE_NORM_CSV" og:/tmp/tmdb_kaggle.csv
    
    # Generate SQL file locally
    cat <<EOF > pkg_kaggle_copy.sql
COPY staging_movies_kaggle(tmdb_id,imdb_id,title,original_title,original_language,release_date,runtime,country_iso2,popularity,vote_average,vote_count,budget,revenue) 
FROM '/tmp/tmdb_kaggle.csv' 
WITH (FORMAT csv, HEADER true);
EOF
    
    docker cp pkg_kaggle_copy.sql og:/tmp/pkg_kaggle_copy.sql
    docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -f /tmp/pkg_kaggle_copy.sql'"
    
    # Cleanup
    docker exec og rm -f /tmp/tmdb_kaggle.csv /tmp/pkg_kaggle_copy.sql
    rm -f pkg_kaggle_copy.sql
    
    # 1.3 Merge
    echo "Merging Kaggle data into Core..."
    docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -1'" < 03_merge_kaggle_into_core.sql
    
else
    echo "Warning: $KAGGLE_CSV not found. Skipping Kaggle baseline import."
fi

# 2. Incremental Catch-up using TMDB API
echo "--- [2/2] TMDB Delta Update ---"

# 2.1 Fetch Deltas
echo "Reading last sync date from DB..."
# Capture output via -tA -f -
LAST_SYNC=$(docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -tA'" < 04_read_last_sync.sql)
# Trim potential whitespace
LAST_SYNC=$(echo "$LAST_SYNC" | xargs)

if [ -z "$LAST_SYNC" ]; then
    LAST_SYNC="2019-12-31" # Fallback
fi
echo "Last sync date: $LAST_SYNC"

echo "Fetching changes from TMDB API..."
python3 tmdb_fetch_delta.py \
  --start-date "$LAST_SYNC" \
  --out "$TMDB_DELTA_CSV"

if [ -f "$TMDB_DELTA_CSV" ]; then
    # 2.2 Load Delta Staging
    echo "Loading TMDB Delta staging..."
    # Run the SQL to truncate/prepare
    docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -1'" < 05_load_tmdb_delta_staging.sql
    
    # Copy data
    # Perform the data load via COPY FROM FILE
    docker cp "$TMDB_DELTA_CSV" og:/tmp/tmdb_delta.csv
    
    # Generate SQL file locally
    cat <<EOF > pkg_delta_copy.sql
COPY staging_movies_tmdb_delta(tmdb_id,imdb_id,title,original_title,original_language,release_date,runtime,country_iso2,popularity,vote_average,vote_count,budget,revenue) 
FROM '/tmp/tmdb_delta.csv' 
WITH (FORMAT csv, HEADER true);
EOF

    docker cp pkg_delta_copy.sql og:/tmp/pkg_delta_copy.sql
    docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -f /tmp/pkg_delta_copy.sql'"
    
    # Cleanup
    docker exec og rm -f /tmp/tmdb_delta.csv /tmp/pkg_delta_copy.sql
    rm -f pkg_delta_copy.sql

    # 2.3 Merge Delta
    echo "Merging TMDB Delta into Core..."
    docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -1'" < 06_merge_tmdb_delta_into_core.sql

else
    echo "No delta CSV produced (maybe no changes or error)."
fi

# 3. Validation
echo "--- Validation ---"
docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -1'" < 07_validate_and_log.sql

echo "=== Daily Update Complete ==="
