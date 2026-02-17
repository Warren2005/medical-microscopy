# Running Instructions

## Prerequisites

- macOS with Homebrew
- Python 3.11
- Node.js (for Electron/React frontend)

---

## Step 1 — Install & Start Services

### PostgreSQL

```bash
brew install postgresql@16
brew services start postgresql@16
createdb medical_microscopy
```

### Qdrant

```bash
brew install qdrant/tap/qdrant

# Run in a dedicated terminal tab (foreground process)
qdrant
```

If the Homebrew tap isn't available, download the binary directly:

```bash
curl -LO https://github.com/qdrant/qdrant/releases/download/v1.7.4/qdrant-aarch64-apple-darwin.tar.gz
tar -xzf qdrant-aarch64-apple-darwin.tar.gz
./qdrant
```

### MinIO

```bash
brew install minio/stable/minio

# Run in a dedicated terminal tab (foreground process)
minio server ~/minio-data
```

Default credentials: `minioadmin` / `minioadmin`

---

## Step 2 — Start the Backend

```bash
cd backend
source venv/bin/activate

# Apply the database migration (first time only)
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload
```

The backend runs at http://localhost:8000.

---

## Step 3 — Validate Everything Is Healthy

```bash
curl http://localhost:8000/api/v1/health
```

You should see:

```json
{
  "status": "healthy",
  "services": {
    "api": "up",
    "postgres": "up",
    "qdrant": "up",
    "minio": "up",
    "clip": "up"
  }
}
```

If any service shows `"down"`, check that it is running in its terminal tab.

You can also view the interactive API docs at http://localhost:8000/docs.

---

## Step 4 — Download & Ingest the Dataset

### Download ISIC 2019

```bash
mkdir -p backend/data/isic2019
cd backend/data/isic2019

# Download metadata CSVs
curl -O https://isic-challenge-data.s3.amazonaws.com/2019/ISIC_2019_Training_GroundTruth.csv
curl -O https://isic-challenge-data.s3.amazonaws.com/2019/ISIC_2019_Training_Metadata.csv

# Download training images (~9GB)
curl -O https://isic-challenge-data.s3.amazonaws.com/2019/ISIC_2019_Training_Input.zip
unzip ISIC_2019_Training_Input.zip
```

Your directory should look like:

```
backend/data/isic2019/
├── ISIC_2019_Training_GroundTruth.csv
├── ISIC_2019_Training_Metadata.csv
└── ISIC_2019_Training_Input/
    ├── ISIC_0000000.jpg
    ├── ISIC_0000001.jpg
    └── ... (25,331 images)
```

### Run Ingestion

```bash
cd backend
source venv/bin/activate

# Test with a small batch first
python -m scripts.ingest_isic --data-dir ./data/isic2019 --limit 10

# Run the full dataset
python -m scripts.ingest_isic --data-dir ./data/isic2019
```

The script is resumable. If interrupted, re-run the same command and it skips already-processed images.

### Verify Data Landed

```bash
# PostgreSQL
psql medical_microscopy -c "SELECT COUNT(*) FROM images;"

# Qdrant
curl http://localhost:6333/collections/medical_images

# MinIO web console
open http://localhost:9000
```

---

## Step 5 — Start the Frontend

```bash
cd frontend
npm run start
```

This builds the React app with Vite and opens the Electron desktop window.

- Drag a microscopy image onto the drop zone
- View the top-10 similar cases in the results grid
- Click a result for full metadata
- Use filter dropdowns to narrow by diagnosis or classification

---

## Quick Test (API only, no frontend needed)

```bash
curl -X POST http://localhost:8000/api/v1/search/similar \
  -F "file=@backend/data/isic2019/ISIC_2019_Training_Input/ISIC_0000000.jpg"
```

---

## Stopping Services

```bash
# PostgreSQL
brew services stop postgresql@16

# Qdrant and MinIO — Ctrl+C in their terminal tabs
```

---

## Terminal Tabs Summary

You need 4 terminal tabs running simultaneously:

| Tab | Command |
|-----|---------|
| 1   | `qdrant` |
| 2   | `minio server ~/minio-data` |
| 3   | `cd backend && source venv/bin/activate && uvicorn app.main:app --reload` |
| 4   | `cd frontend && npm run start` |

PostgreSQL runs as a background service via `brew services` and does not need its own tab.
