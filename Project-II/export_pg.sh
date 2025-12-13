#!/bin/bash
set -e

# export_pg.sh: Dump FilmDB from PostgreSQL
# Usage: ./export_pg.sh

OUTPUT_FILE="filmdb_pg.sql"

echo "=== Exporting FilmDB (PostgreSQL) ==="
echo "Target: $OUTPUT_FILE"

# Use pg_dump
# -O: no owner (better portability)
# -x: no privileges/grant
# --inserts: use INSERT commands instead of COPY (optional, but requested implicitly by 'SQL outputs' for portability, though COPY is standard)
# Actually, standard pg_dump usually uses COPY. Let's stick to standard dump unless specific 'inserts' requested.
# Given Section 1.4.1 just says "Produce two SQL outputs", standard dump is best.

docker exec -i pg pg_dump -U postgres -d filmdb -O -x > "$OUTPUT_FILE"

echo "[OK] Export complete: $OUTPUT_FILE"
ls -lh "$OUTPUT_FILE"
