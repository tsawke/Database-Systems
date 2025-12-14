#!/bin/bash
set -e

# run_with_cpu_limit.sh: Run a command with limited CPU affinity (Cores 0-2)
# Usage: ./run_with_cpu_limit.sh <command> [args...]

if [ $# -eq 0 ]; then
  echo "Usage: $0 <command> [args...]"
  echo "Example: $0 ./daily_update_pg.sh"
  exit 1
fi

echo "=== Running command with limited CPU affinity (Cores 0-1) ==="
echo "Command: $@"

# CRITICAL: taskset only limits the client process. To protect the system,
# we must strictly pin the database containers to the same cores so they don't leak onto Core 2/3.
if command -v docker >/dev/null 2>&1; then
    echo "[INFO] Enforcing CPU pinning (0-1) on 'pg' and 'og' containers..."
    docker update --cpuset-cpus 0-1 pg >/dev/null 2>&1 || true
    docker update --cpuset-cpus 0-1 og >/dev/null 2>&1 || true
fi

# taskset -c 0-1 binds the process to logical cores 0 and 1.
# Child processes will inherit this affinity.
taskset -c 0-1 "$@"
