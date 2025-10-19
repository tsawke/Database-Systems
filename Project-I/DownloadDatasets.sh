# #!/usr/bin/env bash
# # download_openflights.sh
# set -euo pipefail

# DATA_DIR="${1:-$PWD/data/openflights}"
# mkdir -p "$DATA_DIR"
# cd "$DATA_DIR"

# # 从 GitHub 主仓库抓取最新 CSV（.dat 即逗号分隔 CSV）
# # Fetch latest CSVs from the official repo
# curl -L -o airports.dat  https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat
# curl -L -o airlines.dat  https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat
# curl -L -o routes.dat    https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat
# curl -L -o planes.dat    https://raw.githubusercontent.com/jpatokal/openflights/master/data/planes.dat
# curl -L -o countries.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/countries.dat

# # 快速查看每个文件前 3 行 / Peek first 3 lines
# for f in airports.dat airlines.dat routes.dat planes.dat countries.dat; do
#   echo "==> $f"; head -n 3 "$f"
# done


mkdir -p ./data/clickstream && cd ./data/clickstream
wget -c https://dumps.wikimedia.org/other/clickstream/2025-09/clickstream-enwiki-2025-09.tsv.gz
