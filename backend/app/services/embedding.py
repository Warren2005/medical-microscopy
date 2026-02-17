"""
CLIP embedding service using open_clip.

Loads ViT-B/32 model once at startup.
Exposes get_embedding() to convert image bytes to a 512-dim normalized vector.
"""

import io
import time
from typing import Optional

import open_clip
import torch
from PIL import Image

from app.core.config import settings
from app.core.logging_config import logger


class EmbeddingService:
    def __init__(self, model_name: str, device: str):
        self._model_name = model_name
        self._device = device
        self.model = None
        self._preprocess = None

    @property
    def clip_model_name(self) -> str:
        """Convert 'ViT-B/32' to 'ViT-B-32' for open_clip."""
        return self._model_name.replace("/", "-")

    async def load_model(self):
        """Load the CLIP model. Called once at startup."""
        start = time.time()
        self.model, _, self._preprocess = open_clip.create_model_and_transforms(
            self.clip_model_name, pretrained="openai", device=self._device
        )
        self.model.eval()
        elapsed = time.time() - start
        logger.info(
            f"CLIP model loaded in {elapsed:.2f}s",
            extra={"model": self.clip_model_name, "device": self._device},
        )

    async def get_embedding(self, image_bytes: bytes) -> list[float]:
        """Convert image bytes to a 512-dim L2-normalized embedding vector."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_tensor = self._preprocess(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            embedding = self.model.encode_image(image_tensor)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.squeeze().cpu().tolist()

    def health_check(self) -> bool:
        return self.model is not None


embedding_service = EmbeddingService(
    model_name=settings.clip_model_name,
    device=settings.clip_device,
)
