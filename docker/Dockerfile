# docker/Dockerfile
FROM python:3.11-slim

# Avoid prompts in apt and improves logs
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# System libaries (faiss-cpu often needs libgomp1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installing dependencies first 
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm

# Copy code
COPY . .

# Default variables
ENV ENV=dev \
    LOG_LEVEL=INFO \
    DATA_DIR=/app/data \
    INDEX_DIR=/app/data/index \
    DB_PATH=/app/data/meta.duckdb \
    EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

EXPOSE 8000

# Uvicorn with autoreload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
