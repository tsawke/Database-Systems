#!/bin/bash
set -e

# validate_all.sh: Run validation checks on both PostgreSQL and openGauss
# Usage: ./run_with_cpu_limit.sh ./validate_all.sh

echo "=== Starting Validation for FilmDB ==="

# PostgreSQL Validation
echo "--- [1/2] Validating PostgreSQL (pg) ---"
if docker ps | grep -q "pg"; then
    docker exec -i pg psql -U postgres -d filmdb -v ON_ERROR_STOP=1 -f /dev/stdin < 07_validate_and_log.sql
else
    echo "[WARN] Container 'pg' not found or not running."
fi

echo ""

# openGauss Validation
echo "--- [2/2] Validating openGauss (og) ---"
if docker ps | grep -q "og"; then
    docker exec -i og bash -lc "su - omm -c 'gsql -d filmdb -p 5432 -v ON_ERROR_STOP=on -1'" < 07_validate_and_log.sql
else
    echo "[WARN] Container 'og' not found or not running."
fi

echo "=== Validation Complete ==="
