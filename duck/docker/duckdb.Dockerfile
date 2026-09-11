FROM python:3.12-slim-bookworm
RUN pip install --no-cache-dir duckdb==1.3.2
WORKDIR /app
COPY benchmark/common.py benchmark/duckdb_benchmark.py benchmark/duckdb_compaction.py ./
ENTRYPOINT ["python", "duckdb_benchmark.py"]
