"""
ISIC 2019 Dataset Ingestion Script.

Downloads images and metadata from the ISIC 2019 challenge dataset,
generates CLIP embeddings, and stores everything in MinIO, Qdrant,
and PostgreSQL.

Usage:
    cd backend
    python -m scripts.ingest_isic --data-dir ./data/isic2019 --batch-size 32
    python -m scripts.ingest_isic --data-dir ./data/isic2019 --limit 100  # first 100 only

Resumability:
    Tracks progress in a local SQLite checkpoint file (.ingest_checkpoint.db).
    Re-running skips already-processed images.
"""

import argparse
import asyncio
import csv
import logging
import sqlite3
import time
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.models.image import Image
from app.services.database import db_service
from app.services.embedding import embedding_service
from app.services.qdrant import qdrant_service
from app.services.storage import storage_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class IngestionCheckpoint:
    """SQLite-based checkpoint tracker for resumability."""

    def __init__(self, checkpoint_path: Path):
        self._conn = sqlite3.connect(str(checkpoint_path))
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS processed (image_name TEXT PRIMARY KEY)"
        )
        self._conn.commit()

    def is_processed(self, image_name: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM processed WHERE image_name=?", (image_name,)
        ).fetchone()
        return row is not None

    def mark_processed(self, image_name: str):
        self._conn.execute(
            "INSERT OR IGNORE INTO processed (image_name) VALUES (?)", (image_name,)
        )
        self._conn.commit()

    def count_processed(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM processed").fetchone()
        return row[0]

    def close(self):
        self._conn.close()


def load_metadata(data_dir: Path) -> dict[str, dict]:
    """
    Load ISIC 2019 metadata and ground truth CSVs.

    Returns a dict mapping image_name -> metadata dict.
    """
    metadata = {}

    # Load ground truth (diagnosis labels)
    gt_path = data_dir / "ISIC_2019_Training_GroundTruth.csv"
    if gt_path.exists():
        with open(gt_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                image_name = row.get("image", "")
                # Ground truth has binary columns: MEL, NV, BCC, AK, BKL, DF, VASC, SCC
                # Find the diagnosis with value "1.0" or "1"
                diagnosis = None
                diagnosis_map = {
                    "MEL": "melanoma",
                    "NV": "melanocytic_nevus",
                    "BCC": "basal_cell_carcinoma",
                    "AK": "actinic_keratosis",
                    "BKL": "benign_keratosis",
                    "DF": "dermatofibroma",
                    "VASC": "vascular_lesion",
                    "SCC": "squamous_cell_carcinoma",
                }
                for code, name in diagnosis_map.items():
                    if row.get(code, "0") in ("1.0", "1"):
                        diagnosis = name
                        break
                metadata[image_name] = {"diagnosis": diagnosis}
        logger.info(f"Loaded ground truth for {len(metadata)} images")

    # Load metadata (age, sex, anatomical site)
    meta_path = data_dir / "ISIC_2019_Training_Metadata.csv"
    if meta_path.exists():
        with open(meta_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                image_name = row.get("image", "")
                if image_name not in metadata:
                    metadata[image_name] = {}
                metadata[image_name].update(
                    {
                        "age_approx": row.get("age_approx", ""),
                        "sex": row.get("sex", ""),
                        "anatom_site": row.get("anatom_site_general", ""),
                    }
                )
        logger.info(f"Loaded metadata for {len(metadata)} images")

    return metadata


def classify_benign_malignant(diagnosis: str | None) -> str | None:
    """Classify diagnosis as benign or malignant."""
    if not diagnosis:
        return None
    malignant = {"melanoma", "basal_cell_carcinoma", "squamous_cell_carcinoma"}
    benign = {
        "melanocytic_nevus",
        "benign_keratosis",
        "dermatofibroma",
        "vascular_lesion",
    }
    if diagnosis in malignant:
        return "malignant"
    if diagnosis in benign:
        return "benign"
    return None


async def ingest_single_image(
    image_path: Path,
    metadata_row: dict,
    checkpoint: IngestionCheckpoint,
) -> bool:
    """
    Process one image: upload to MinIO, embed with CLIP, insert into PG + Qdrant.

    Returns True if processed, False if skipped.
    """
    image_name = image_path.stem

    if checkpoint.is_processed(image_name):
        return False

    image_bytes = image_path.read_bytes()
    image_id = uuid4()
    object_name = f"isic2019/{image_name}{image_path.suffix}"

    # Upload to MinIO
    content_type = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    storage_service.upload_image(object_name, image_bytes, content_type)

    # Generate CLIP embedding
    embedding = await embedding_service.get_embedding(image_bytes)

    # Determine diagnosis and classification
    diagnosis = metadata_row.get("diagnosis")
    benign_malignant = classify_benign_malignant(diagnosis)

    # Parse age
    age_str = metadata_row.get("age_approx", "")
    age = None
    if age_str:
        try:
            age = int(float(age_str))
        except (ValueError, TypeError):
            pass

    # Insert into PostgreSQL
    async with db_service.get_session() as session:
        image_record = Image(
            id=image_id,
            dataset_source="ISIC2019",
            image_path=object_name,
            diagnosis=diagnosis,
            tissue_type="skin",
            benign_malignant=benign_malignant,
            age=age,
            sex=metadata_row.get("sex") or None,
        )
        session.add(image_record)
        await session.commit()

    # Insert into Qdrant
    await qdrant_service.upsert(
        id=str(image_id),
        vector=embedding,
        payload={
            "diagnosis": diagnosis,
            "tissue_type": "skin",
            "benign_malignant": benign_malignant,
            "dataset": "ISIC2019",
        },
    )

    checkpoint.mark_processed(image_name)
    return True


async def main():
    parser = argparse.ArgumentParser(description="Ingest ISIC 2019 dataset")
    parser.add_argument(
        "--data-dir",
        required=True,
        help="Path to ISIC 2019 dataset directory",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only first N images (for testing)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return

    # Initialize services
    logger.info("Initializing services...")
    await db_service.connect()
    await qdrant_service.connect()
    await qdrant_service.ensure_collection(vector_size=512)
    storage_service.connect()
    await embedding_service.load_model()

    # Load metadata
    metadata = load_metadata(data_dir)

    # Set up checkpoint
    checkpoint_path = data_dir / ".ingest_checkpoint.db"
    checkpoint = IngestionCheckpoint(checkpoint_path)
    already_done = checkpoint.count_processed()
    if already_done > 0:
        logger.info(f"Resuming: {already_done} images already processed")

    # Find images
    image_dir = data_dir / "ISIC_2019_Training_Input"
    if not image_dir.exists():
        # Try the data_dir itself as the image directory
        image_dir = data_dir
    images = sorted(image_dir.glob("*.jpg")) + sorted(image_dir.glob("*.png"))
    if args.limit:
        images = images[: args.limit]

    logger.info(f"Found {len(images)} images to process")
    start_time = time.time()
    processed = 0
    skipped = 0

    for i, image_path in enumerate(images):
        image_name = image_path.stem
        meta = metadata.get(image_name, {})

        try:
            was_processed = await ingest_single_image(image_path, meta, checkpoint)
            if was_processed:
                processed += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"Failed to process {image_name}: {e}")
            continue

        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (processed + skipped) / elapsed if elapsed > 0 else 0
            logger.info(
                f"Progress: {i + 1}/{len(images)} "
                f"(processed={processed}, skipped={skipped}, "
                f"rate={rate:.1f} img/s)"
            )

    elapsed = time.time() - start_time
    logger.info(
        f"Done: processed={processed}, skipped={skipped}, "
        f"total_time={elapsed:.1f}s"
    )

    # Cleanup
    checkpoint.close()
    await db_service.disconnect()
    await qdrant_service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
