from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
QDRANT_HOST = os.getenv("QDRANT_HOST")

app = FastAPI(title="Medical Microscopy API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Medical Microscopy API", "status": "ok"}

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "services": {
            "api": "up"
            # Will add postgres, qdrant, minio later
        }
    }