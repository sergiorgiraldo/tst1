import csv
import json
import sys

record = json.load(open(sys.argv[1]))
with open(sys.argv[2], "a", newline="") as output:
    csv.writer(output).writerow([
        record["experiment"], record["engine"], record["run"], record["startup_seconds"],
        record["query_seconds"], record["total_seconds"], record["result_hash"],
    ])
