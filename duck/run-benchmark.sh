#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p data results

if [[ ! -f .env ]]; then
  cp .env.example .env
fi
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  if [[ -z "${!key+x}" ]]; then
    printf -v "$key" '%s' "$value"
    export "$key"
  fi
done < .env

echo "Building benchmark images..."
docker compose build

if [[ ! -f data/manifest.json ]] || [[ "${REGENERATE_DATA:-0}" == "1" ]]; then
  echo "Generating ${PARQUET_FILES} Parquet files with ${ROWS_PER_FILE} rows each..."
  docker compose run --rm generate
else
  echo "Using existing dataset described by data/manifest.json (set REGENERATE_DATA=1 to replace it)."
fi

rm -f results/*.json results/results.csv results/summary.txt
mkdir -p results/compacted
printf 'experiment,engine,run,startup_seconds,processing_seconds,total_seconds,result_hash\n' > results/results.csv

run_one() {
  local experiment="$1"
  local engine="$2"
  local kind="$3"
  local number="$4"
  local service="$engine"
  [[ "$experiment" == "compaction" ]] && service="${engine}-compact"
  local output="/results/${experiment}-${engine}-${kind}-${number}.json"
  docker compose run --rm \
    -e RUN_KIND="$kind" -e RUN_NUMBER="$number" -e RESULT_FILE="$output" \
    "$service"
  if [[ "$kind" == "measured" ]]; then
    python3 scripts/append_result.py "results/${experiment}-${engine}-${kind}-${number}.json" results/results.csv
  fi
}

for ((run=1; run<=WARMUP_RUNS; run++)); do
  echo "Warmup $run/$WARMUP_RUNS"
  run_one query duckdb warmup "$run"
  run_one query spark warmup "$run"
  run_one compaction duckdb warmup "$run"
  run_one compaction spark warmup "$run"
done

for ((run=1; run<=MEASURED_RUNS; run++)); do
  echo "Measured run $run/$MEASURED_RUNS"
  if (( run % 2 == 1 )); then engines=(duckdb spark); else engines=(spark duckdb); fi
  for engine in "${engines[@]}"; do run_one query "$engine" measured "$run"; done
  for engine in "${engines[@]}"; do run_one compaction "$engine" measured "$run"; done
done

python3 scripts/summarize.py results/*.json | tee results/summary.txt
