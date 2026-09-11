import json
import statistics
import sys

records = [json.load(open(path)) for path in sys.argv[1:] if "measured" in path]
print("\nBenchmark summary (measured runs only)")

for experiment in ("query", "compaction"):
    selected = [r for r in records if r["experiment"] == experiment]
    hashes = {record["result_hash"] for record in selected}
    if len(hashes) != 1:
        raise SystemExit(f"ERROR: {experiment} results differ between engines: {sorted(hashes)}")

    print(f"\n{experiment.upper()} — results match: yes")
    print(f"{'engine':<10} {'median process':>16} {'mean process':>14} {'median total':>14}")
    for engine in ("duckdb", "spark"):
        values = [r for r in selected if r["engine"] == engine]
        process = [r["query_seconds"] for r in values]
        total = [r["total_seconds"] for r in values]
        print(f"{engine:<10} {statistics.median(process):>14.3f}s "
              f"{statistics.mean(process):>12.3f}s {statistics.median(total):>12.3f}s")

    duck = statistics.median(r["query_seconds"] for r in selected if r["engine"] == "duckdb")
    spark = statistics.median(r["query_seconds"] for r in selected if r["engine"] == "spark")
    winner = "DuckDB" if duck < spark else "Spark"
    ratio = max(duck, spark) / min(duck, spark)
    print(f"Median processing winner: {winner} ({ratio:.2f}x faster in this local test)")
