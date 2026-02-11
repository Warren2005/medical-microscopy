#!/bin/bash

echo "Starting Medical Microscopy Services..."

# Start PostgreSQL (if not auto-started)
brew services start postgresql@15

# Start Qdrant
echo "Starting Qdrant..."
~/Services/qdrant/qdrant &
QDRANT_PID=$!

# Start MinIO
echo "Starting MinIO..."
minio server ~/minio-data --console-address ":9001" &
MINIO_PID=$!

echo "Services started!"
echo "Qdrant: http://localhost:6333"
echo "MinIO: http://localhost:9001"
echo "PostgreSQL: localhost:5432"

echo ""
echo "To stop services, run: kill $QDRANT_PID $MINIO_PID"