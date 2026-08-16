FROM python:3.12-slim-bookworm
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pyspark==4.0.0
WORKDIR /app
COPY benchmark/common.py benchmark/spark_benchmark.py benchmark/spark_compaction.py ./
ENTRYPOINT ["python", "spark_benchmark.py"]
