# DuckDB vs Spark: query and compact 1,000 Parquet files

A reproducible, local Docker benchmark comparing DuckDB and Apache Spark while querying and compacting the same Parquet dataset. It is inspired by Matt Martin's [1,000 JSON files from S3 comparison](https://performancede.substack.com/p/querying-1-thousand-json-files-from), but isolates the execution engines on one machine and uses Parquet.

## What the benchmark measures

The generator creates 1,000 deterministic Snappy-compressed Parquet files. Following the source project's skew experiment, 998 contain 5,000 rows and 2 contain 100,000 rows by default (5.19 million rows total). Both engines run the same analytical query: filter nine months of events, group by region and category, and calculate count, revenue, and average price.

Each engine receives the same Docker CPU and memory limits. The runner performs a warmup, alternates which engine runs first, records five fresh-process measurements, and rejects the benchmark if the engines' result hashes differ.

The second experiment reads every source file and writes one Zstandard-compressed Parquet data file per engine, ordered by `event_id`. It times the complete read, sort, and write operation. Read-back validation—row count, quantity sum, and event ID sum—is outside the timed section, and the run fails if the engines disagree.

Two timings are reported:

- **query**: execution and collection of the final 20 aggregate rows. For Spark, creating the lazy input DataFrame is outside this timer, but actual Parquet reading happens inside it.
- **total**: engine startup plus query time. This exposes Spark's JVM/session startup cost, which matters for short-lived jobs.

This is a single-node test, not a claim that DuckDB replaces distributed Spark. Spark's strength is data or concurrency beyond one machine; this project tests the common case where a workload fits on one machine.

## Requirements

- Docker Desktop (or Docker Engine with Compose v2)
- At least 10 GB free disk space available to Docker
- Recommended: 8 GB of memory and 4 CPUs available to Docker
- macOS, Linux, or Windows through WSL2

No local Python, Java, DuckDB, or Spark installation is required. Python 3 is used only by the host runner to combine tiny JSON result files; macOS and most Linux distributions already include it.

The Python images are pinned to Debian Bookworm so Spark's Java 17 dependency remains available even when Docker's default `slim` distribution changes.

## Run it

```bash
cd ~/tmp/playground/duck
cp .env.example .env
./run-benchmark.sh
```

The first run downloads/builds images, generates the dataset, warms up both engines, and runs five measurements per engine. Depending on the machine and network, it can take several minutes. Later runs reuse `data/`.

Results are written to:

- `results/summary.txt` — readable median/mean summary
- `results/results.csv` — measured runs for plotting or analysis
- `results/*.json` — complete per-run metadata and correctness hashes
- `results/compacted/duckdb.parquet` — DuckDB's final compacted file
- `results/compacted/spark/` — Spark's final compacted dataset (one Parquet data file plus metadata)
- `data/manifest.json` — generated dataset description

## Fast smoke test

To verify the complete setup with 50 small files:

```bash
make quick
```

This deliberately replaces the current dataset. To return to the full benchmark, run:

```bash
REGENERATE_DATA=1 ./run-benchmark.sh
```

Values from `.env` still determine the restored dataset size.

## Configure the experiment

Edit `.env` before running:

```dotenv
PARQUET_FILES=1000
ROWS_PER_FILE=5000
LARGE_FILE_COUNT=2
LARGE_FILE_MULTIPLIER=20
WARMUP_RUNS=1
MEASURED_RUNS=5
BENCHMARK_CPUS=4
BENCHMARK_MEMORY=8g
```

After changing `PARQUET_FILES` or `ROWS_PER_FILE`, force regeneration:

```bash
REGENERATE_DATA=1 ./run-benchmark.sh
```

`LARGE_FILE_COUNT=2` and `LARGE_FILE_MULTIPLIER=20` reproduce the source experiment's basic file-size-skew shape in Parquet. Set `LARGE_FILE_COUNT=0` for uniformly sized files. For a heavier test, raise `ROWS_PER_FILE` to `50000` and ensure Docker has sufficient disk and memory. Keep the CPU/memory limits identical between engines.

## Useful commands

```bash
# Generate/re-generate only the dataset
make generate

# Run benchmark using an existing dataset
make benchmark

# Remove containers, generated data, and results
make clean

# Inspect raw measurements
column -s, -t results/results.csv
```

## Reading the result responsibly

Compare medians, not the fastest individual run. Query time is the closest engine-to-engine comparison; total time represents short-lived batch jobs. Docker Desktop's VM, laptop thermal throttling, background activity, filesystem cache, and architecture all affect the numbers. Run on an otherwise idle machine and publish the `.env`, `data/manifest.json`, Docker allocation, CPU model, and all CSV rows with any reported result.

The [source benchmark repository](https://github.com/mattmartin14/dream_machine/tree/main/substack/articles/2026.08.12-duckdb_vs_spark_emr) compares DuckDB on ECS Fargate with Spark on EMR Serverless over S3 JSON, deliberately includes two oversized inputs, and separates logical processing from service startup. This project retains the 1,000-file/skew idea and separate startup timing, but intentionally removes cloud service, network, and S3 request variability so it answers a narrower question: how the engines compare over the same local Parquet files with equal resources. It is not a numerical reproduction of the article.

## Troubleshooting

- **Docker daemon error:** start Docker Desktop and wait until it reports that the engine is running.
- **Container is killed / exit 137:** increase Docker Desktop memory or lower `BENCHMARK_MEMORY` and `ROWS_PER_FILE`.
- **`no matching manifest`:** rebuild with `docker compose build --no-cache`; all chosen base images support common Intel and Apple Silicon systems.
- **Old data was reused:** set `REGENERATE_DATA=1` when changing dataset settings.
- **Result hash mismatch:** keep the JSON files and report the exact images/architecture. The runner stops instead of presenting invalid timing results.

## Project layout

```text
benchmark/       data generation and engine workloads
docker/          pinned, engine-specific images
scripts/         result collection and validation
compose.yaml     equal resource limits and shared volumes
run-benchmark.sh full experiment orchestration
```
