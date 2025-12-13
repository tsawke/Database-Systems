#!/bin/bash
set -e

# init_pg.sh: Initialize FilmDB (Project II) on PostgreSQL
# Usage reference: Tutorial for Database Setup (One-liners)

echo "=== Initializing PostgreSQL for FilmDB (Project II) ==="

# 1. Re-create the filmdb database
echo "[1/3] Creating database 'filmdb'..."
docker exec -i pg psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS filmdb;"
docker exec -i pg psql -U postgres -d postgres -c "CREATE DATABASE filmdb;"

# 2. Load legacy filmdb.sql
# Note: filmdb.sql contains SQLite directives (PRAGMA) which we strip out.
echo "[2/3] Loading legacy 'filmdb.sql'..."
sed '/^PRAGMA/d' filmdb.sql | docker exec -i pg psql -U postgres -d filmdb -v ON_ERROR_STOP=1

# 3. Apply Schema Enhancement
# Note: Using the one-liner style for local file input
echo "[3/3] Applying '01_schema_enhancement.sql'..."
docker exec -i pg psql -U postgres -d filmdb -v ON_ERROR_STOP=1 -1 < 01_schema_enhancement.sql

echo "=== PostgreSQL Initialization Complete ==="
