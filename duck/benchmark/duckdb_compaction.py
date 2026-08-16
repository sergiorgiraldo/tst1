import os
import time
from pathlib import Path

import duckdb

from common import timed, write_result

run_kind = os.environ.get("RUN_KIND", "measured")
run_number = int(os.environ.get("RUN_NUMBER", "1"))
threads = int(os.environ.get("BENCHMARK_THREADS", "4"))
output = Path("/results/compacted/duckdb.parquet")
output.parent.mkdir(parents=True, exist_ok=True)
output.unlink(missing_ok=True)

started = time.perf_counter()
connection = duckdb.connect(":memory:")
connection.execute(f"SET threads = {threads}")
startup_s = time.perf_counter() - started

copy_sql = f"""
COPY (
  SELECT * FROM read_parquet('/data/parquet/*.parquet')
  ORDER BY event_id
) TO '{output}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)
"""
_, processing_s = timed(lambda: connection.execute(copy_sql))

# Read-back validation is intentionally outside the timed processing path.
row = connection.execute(f"""
SELECT count(*), sum(quantity), sum(event_id)
FROM read_parquet('{output}')
""").fetchone()
verification = [("all", "all", int(row[0]), int(row[1]), int(row[2]))]
write_result(
    "duckdb", run_kind, run_number, startup_s, processing_s, verification,
    {"version": duckdb.__version__, "threads": threads, "output_rows": int(row[0]),
     "output_bytes": output.stat().st_size, "output_path": str(output)},
    experiment="compaction",
)
