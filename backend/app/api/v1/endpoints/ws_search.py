"""
WebSocket endpoint for streaming search results.

Streams results progressively as they are found, allowing the frontend
to render results one-by-one for perceived performance improvement.
"""

import json
import time
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.logging_config import logger
from app.models.image import Image
from app.services.database import db_service
from app.services.embedding import embedding_service
from app.services.qdrant import qdrant_service
from app.services.storage import storage_service
from app.services.search_helpers import build_qdrant_filter

router = APIRouter()


@router.websocket("/ws/search")
async def websocket_search(websocket: WebSocket):
    """
    WebSocket search endpoint.

    Client sends a JSON message with base64 image data:
    {
        "image_base64": "<base64 encoded image>",
        "limit": 10,
        "diagnosis": null,
        "tissue_type": null,
        "benign_malignant": null
    }

    Server streams results back one at a time:
    {"type": "status", "message": "Generating embedding..."}
    {"type": "status", "message": "Searching..."}
    {"type": "result", "index": 0, "data": {...}}
    {"type": "result", "index": 1, "data": {...}}
    {"type": "complete", "total": 10, "total_time_ms": 1234.5}
    """
    await websocket.accept()

    try:
        while True:
            # Receive search request
            data = await websocket.receive_text()
            request = json.loads(data)

            import base64
            image_base64 = request.get("image_base64", "")
            limit = request.get("limit", 10)
            diagnosis = request.get("diagnosis")
            tissue_type = request.get("tissue_type")
            benign_malignant = request.get("benign_malignant")

            total_start = time.time()

            # Step 1: Generate embedding
            await websocket.send_json({"type": "status", "message": "Generating embedding..."})
            image_bytes = base64.b64decode(image_base64)
            embed_start = time.time()
            embedding = await embedding_service.get_embedding(image_bytes)
            embed_time = (time.time() - embed_start) * 1000

            # Step 2: Search Qdrant
            await websocket.send_json({
                "type": "status",
                "message": "Searching database...",
                "embedding_time_ms": round(embed_time, 1),
            })

            query_filter = build_qdrant_filter(diagnosis, tissue_type, benign_malignant)
            qdrant_results = await qdrant_service.search(
                vector=embedding, limit=limit, query_filter=query_filter
            )

            # Step 3: Stream results one by one
            for idx, point in enumerate(qdrant_results):
                image_id = UUID(str(point.id))

                async with db_service.get_session() as session:
                    stmt = select(Image).where(Image.id == image_id)
                    result = await session.execute(stmt)
                    image = result.scalar_one_or_none()

                if image:
                    url = storage_service.get_presigned_url(image.image_path)
                    await websocket.send_json({
                        "type": "result",
                        "index": idx,
                        "data": {
                            "image": {
                                "id": str(image.id),
                                "dataset_source": image.dataset_source,
                                "image_path": image.image_path,
                                "diagnosis": image.diagnosis,
                                "tissue_type": image.tissue_type,
                                "benign_malignant": image.benign_malignant,
                                "age": image.age,
                                "sex": image.sex,
                            },
                            "similarity_score": point.score,
                            "image_url": url,
                        },
                    })

            # Step 4: Send completion
            total_time = (time.time() - total_start) * 1000
            await websocket.send_json({
                "type": "complete",
                "total": len(qdrant_results),
                "total_time_ms": round(total_time, 1),
                "embedding_time_ms": round(embed_time, 1),
            })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
