#!/bin/bash
set -e

# export_og.sh: Dump FilmDB from openGauss
# Usage: ./export_og.sh

OUTPUT_FILE="filmdb_og.sql"

echo "=== Exporting FilmDB (openGauss) ==="
echo "Target: $OUTPUT_FILE"

# openGauss uses gs_dump
# Usage inside container: gs_dump -U omm -f /tmp/dump.sql filmdb
# Then copy out? Or pipe stdout? gs_dump usually writes to file.
# Note: gs_dump requires -f for file usually, but -f - might work for stdout?
# Let's try piping. If gs_dump doesn't support stdout easily (it usually does via -f -), we might need a temp file.
# Documentation says gs_dump ... -f <filename>. 
# Safer approach: dump to internal path, then cat out.

DUMP_PATH="/var/lib/opengauss/data/filmdb_og_temp.sql"

echo "Running gs_dump inside container..."
docker exec -i og bash -lc "su - omm -c 'gs_dump -p 5432 -f $DUMP_PATH -n public -F p filmdb'" 
# -F p: plain text
# -n public: schema (optional, but cleaner)

echo "Copying dump to host..."
# Using docker exec cat to stream it out
docker exec -i og bash -lc "cat $DUMP_PATH" > "$OUTPUT_FILE"

# Cleanup
echo "Cleaning up container temp file..."
docker exec -i og bash -lc "rm -f $DUMP_PATH"

echo "[OK] Export complete: $OUTPUT_FILE"
ls -lh "$OUTPUT_FILE"
