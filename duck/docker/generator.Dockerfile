FROM python:3.12-slim-bookworm
RUN pip install --no-cache-dir numpy==2.2.6 pyarrow==20.0.0
WORKDIR /app
COPY benchmark/generate.py .
CMD ["python", "generate.py"]
