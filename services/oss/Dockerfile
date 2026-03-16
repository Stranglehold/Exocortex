FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2, faiss, sentence-transformers, and Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser and its system dependencies
RUN playwright install chromium --with-deps

# Pre-download the embedding model so container startup is fast
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY src/ ./src/

# FAISS data directory
RUN mkdir -p /app/data/faiss

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 7731

# Start scheduler in background thread, Flask in foreground
CMD ["python", "src/main.py"]
