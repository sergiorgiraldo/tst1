import os
import time

import duckdb

from common import timed, write_result


run_kind = os.environ.get("RUN_KIND", "measured")
run_number = int(os.environ.get("RUN_NUMBER", "1"))
threads = int(os.environ.get("BENCHMARK_THREADS", "4"))
started = time.perf_counter()
connection = duckdb.connect(":memory:")
connection.execute(f"SET threads = {threads}")
startup_s = time.perf_counter() - started
sql = """
SELECT region, category, count(*) AS orders,
       round(sum(quantity * unit_price * (1 - discount)), 4) AS revenue,
       round(avg(unit_price), 6) AS avg_price
FROM read_parquet('/data/parquet/*.parquet')
WHERE event_date >= DATE '2024-04-01' AND event_date < DATE '2025-01-01'
GROUP BY region, category
ORDER BY region, category
"""
rows, query_s = timed(lambda: connection.execute(sql).fetchall())
write_result("duckdb", run_kind, run_number, startup_s, query_s, rows,
             {"version": duckdb.__version__, "threads": threads})
