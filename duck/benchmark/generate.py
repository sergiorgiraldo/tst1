import json
import os
import shutil
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


file_count = int(os.environ.get("PARQUET_FILES", "1000"))
rows_per_file = int(os.environ.get("ROWS_PER_FILE", "5000"))
large_file_count = int(os.environ.get("LARGE_FILE_COUNT", "2"))
large_file_multiplier = int(os.environ.get("LARGE_FILE_MULTIPLIER", "20"))
if not 0 <= large_file_count <= file_count:
    raise ValueError("LARGE_FILE_COUNT must be between zero and PARQUET_FILES")
root = Path("/data/parquet")
staging = Path("/data/parquet.building")
if staging.exists():
    shutil.rmtree(staging)
staging.mkdir(parents=True)

regions = np.array(["eu", "us", "apac", "latam"])
categories = np.array(["books", "electronics", "food", "home", "sports"])
started = time.perf_counter()
next_event_id = 0
file_rows = []

for index in range(file_count):
    rng = np.random.default_rng(42 + index)
    is_large = index >= file_count - large_file_count
    n = rows_per_file * (large_file_multiplier if is_large else 1)
    file_rows.append(n)
    quantity = rng.integers(1, 11, n, dtype=np.int16)
    unit_price = np.round(rng.uniform(2.0, 500.0, n), 2)
    discount = np.round(rng.uniform(0.0, 0.30, n), 4)
    table = pa.table({
        "event_id": np.arange(next_event_id, next_event_id + n, dtype=np.int64),
        "event_date": (np.datetime64("2024-01-01") + rng.integers(0, 366, n).astype("timedelta64[D]")).astype("datetime64[D]"),
        "region": regions[rng.integers(0, len(regions), n)],
        "category": categories[rng.integers(0, len(categories), n)],
        "quantity": quantity,
        "unit_price": unit_price,
        "discount": discount,
    })
    pq.write_table(table, staging / f"part-{index:05d}.parquet", compression="snappy", row_group_size=rows_per_file)
    next_event_id += n
    if (index + 1) % 100 == 0:
        print(f"generated {index + 1}/{file_count} files", flush=True)

if root.exists():
    shutil.rmtree(root)
staging.rename(root)
manifest = {
    "files": file_count,
    "rows_per_file": rows_per_file,
    "large_files": large_file_count,
    "large_file_multiplier": large_file_multiplier,
    "total_rows": sum(file_rows),
    "min_rows_per_file": min(file_rows),
    "max_rows_per_file": max(file_rows),
    "seed_scheme": "42 + file_index",
    "seconds": round(time.perf_counter() - started, 3),
}
Path("/data/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
