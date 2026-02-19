# Multi-stage Dockerfile for the Medical Microscopy backend
# Stage 1: Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system deps for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with gunicorn (production) — uses gunicorn.conf.py
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
