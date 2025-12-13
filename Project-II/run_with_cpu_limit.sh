#!/bin/bash
set -e

# run_with_cpu_limit.sh: Run a command with limited CPU affinity (Cores 0-2)
# Usage: ./run_with_cpu_limit.sh <command> [args...]

if [ $# -eq 0 ]; then
  echo "Usage: $0 <command> [args...]"
  echo "Example: $0 ./daily_update_pg.sh"
  exit 1
fi

echo "=== Running command with limited CPU affinity (Cores 0-2) ==="
echo "Command: $@"

# taskset -c 0-2 binds the process to logical cores 0, 1, and 2.
# Child processes will inherit this affinity.
taskset -c 0-2 "$@"
