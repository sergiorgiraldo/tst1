import hashlib
import json
import os
import time
from pathlib import Path


def timed(action):
    start = time.perf_counter()
    value = action()
    return value, time.perf_counter() - start


def canonical_hash(rows):
    normalized = []
    for row in rows:
        normalized.append([
            row[0], row[1], int(row[2]),
            round(float(row[3]), 6), round(float(row[4]), 6),
        ])
    payload = json.dumps(sorted(normalized), separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def write_result(engine, run_kind, run_number, startup_s, query_s, rows, extra=None, experiment="query"):
    result = {
        "experiment": experiment,
        "engine": engine,
        "run_kind": run_kind,
        "run": run_number,
        "startup_seconds": round(startup_s, 6),
        "query_seconds": round(query_s, 6),
        "total_seconds": round(startup_s + query_s, 6),
        "result_rows": len(rows),
        "result_hash": canonical_hash(rows),
    }
    result.update(extra or {})
    output = Path(os.environ.get("RESULT_FILE", f"/results/{engine}.json"))
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
