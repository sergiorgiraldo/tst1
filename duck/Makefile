.PHONY: benchmark generate clean quick

benchmark:
	./run-benchmark.sh

generate:
	docker compose build generate
	docker compose run --rm generate

quick:
	PARQUET_FILES=50 ROWS_PER_FILE=1000 LARGE_FILE_COUNT=2 LARGE_FILE_MULTIPLIER=5 WARMUP_RUNS=1 MEASURED_RUNS=2 REGENERATE_DATA=1 ./run-benchmark.sh

clean:
	docker compose down --remove-orphans
	rm -rf data results
