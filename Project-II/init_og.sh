#!/bin/bash
set -e

# init_og.sh: Initialize FilmDB (Project II) on openGauss
# Usage reference: Tutorial for Database Setup (One-liners)

echo "=== Initializing openGauss for FilmDB (Project II) ==="

# 1. Re-create the filmdb database
echo "[1/3] Creating database 'filmdb'..."
docker exec -i og bash -lc "su - omm -c 'gsql -d postgres -p 5432 -c \"DROP DATABASE IF EXISTS filmdb;\"'"
docker exec -i og bash -lc "su - omm -c 'gsql -d postgres -p 5432 -c \"CREATE DATABASE filmdb;\"'"

# 2. Load legacy filmdb.sql
# Note: filmdb.sql contains SQLite directives (PRAGMA) which we strip out.
echo "[2/3] Loading legacy 'filmdb.sql'..."
sed '/^PRAGMA/d' filmdb.sql | docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on'"

# 3. Apply Schema Enhancement
# Note: Using the one-liner style for local file input, passing -f - for stdin
echo "[3/3] Applying '01_schema_enhancement.sql'..."
docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -1'" < 01_schema_enhancement.sql

echo "=== openGauss Initialization Complete ==="
