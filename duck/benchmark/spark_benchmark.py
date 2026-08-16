import os
import time

from pyspark.sql import SparkSession

from common import timed, write_result


run_kind = os.environ.get("RUN_KIND", "measured")
run_number = int(os.environ.get("RUN_NUMBER", "1"))
threads = int(os.environ.get("BENCHMARK_THREADS", "4"))
started = time.perf_counter()
spark = (SparkSession.builder
         .master(f"local[{threads}]")
         .appName("parquet-benchmark")
         .config("spark.ui.enabled", "false")
         .config("spark.sql.shuffle.partitions", str(threads))
         .config("spark.driver.memory", os.environ.get("SPARK_DRIVER_MEMORY", "6g"))
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
startup_s = time.perf_counter() - started
spark.read.parquet("/data/parquet/*.parquet").createOrReplaceTempView("events")
sql = """
SELECT region, category, count(*) AS orders,
       round(sum(quantity * unit_price * (1 - discount)), 4) AS revenue,
       round(avg(unit_price), 6) AS avg_price
FROM events
WHERE event_date >= DATE '2024-04-01' AND event_date < DATE '2025-01-01'
GROUP BY region, category
ORDER BY region, category
"""
collected, query_s = timed(lambda: spark.sql(sql).collect())
rows = [tuple(row) for row in collected]
write_result("spark", run_kind, run_number, startup_s, query_s, rows,
             {"version": spark.version, "threads": threads})
spark.stop()
