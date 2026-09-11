import os
import shutil
import time
from pathlib import Path

from pyspark.sql import SparkSession

from common import timed, write_result

run_kind = os.environ.get("RUN_KIND", "measured")
run_number = int(os.environ.get("RUN_NUMBER", "1"))
threads = int(os.environ.get("BENCHMARK_THREADS", "4"))
output = Path("/results/compacted/spark")
shutil.rmtree(output, ignore_errors=True)

started = time.perf_counter()
spark = (SparkSession.builder.master(f"local[{threads}]")
         .appName("parquet-compaction-benchmark")
         .config("spark.ui.enabled", "false")
         .config("spark.sql.shuffle.partitions", str(threads))
         .config("spark.driver.memory", os.environ.get("SPARK_DRIVER_MEMORY", "6g"))
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
startup_s = time.perf_counter() - started

def compact():
    source = spark.read.parquet("/data/parquet/*.parquet")
    (source.orderBy("event_id").coalesce(1).write.mode("overwrite")
     .option("compression", "zstd").parquet(str(output)))

_, processing_s = timed(compact)

# Read-back validation is intentionally outside the timed processing path.
row = spark.read.parquet(str(output)).selectExpr(
    "count(*) AS row_count", "sum(quantity) AS quantity_sum", "sum(event_id) AS event_id_sum"
).first()
verification = [("all", "all", int(row.row_count), int(row.quantity_sum), int(row.event_id_sum))]
parquet_files = list(output.glob("*.parquet"))
write_result(
    "spark", run_kind, run_number, startup_s, processing_s, verification,
    {"version": spark.version, "threads": threads, "output_rows": int(row.row_count),
     "output_bytes": sum(path.stat().st_size for path in parquet_files),
     "output_files": len(parquet_files), "output_path": str(output)},
    experiment="compaction",
)
spark.stop()
