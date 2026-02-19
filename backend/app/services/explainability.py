"""GradCAM-style explainability using CLIP attention maps."""

import asyncio
import io

import numpy as np
import torch
from PIL import Image as PILImage

from app.core.logging_config import logger
from app.services.embedding import embedding_service


class GradCAMService:
    """Generates attention heatmaps from CLIP's vision transformer."""

    def _generate_heatmap(self, image_bytes: bytes) -> bytes:
        """Generate a gradient-based saliency heatmap overlay for an image.

        Uses input-gradient saliency: forward pass through CLIP's vision
        encoder, backpropagate the embedding sum, and use gradient magnitude
        as the spatial attention signal. Returns PNG bytes of the overlay.
        """
        model = embedding_service.model
        preprocess = embedding_service._preprocess
        device = embedding_service._device

        image = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        image_tensor = preprocess(image).unsqueeze(0).to(device)
        image_tensor.requires_grad_(True)

        # Forward + backward to get input gradients
        embedding = model.encode_image(image_tensor)
        embedding.sum().backward()

        gradients = image_tensor.grad.data.abs()
        # Average over colour channels to get a single spatial map
        saliency = gradients.squeeze().mean(dim=0).cpu().numpy()

        # Normalize to [0, 1]
        saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min() + 1e-8)

        # Upscale to original image size
        saliency_pil = PILImage.fromarray((saliency * 255).astype(np.uint8))
        saliency_pil = saliency_pil.resize(image.size, PILImage.BILINEAR)
        saliency_np = np.array(saliency_pil) / 255.0

        # Red-yellow heatmap with semi-transparent alpha
        heatmap = np.zeros((*saliency_np.shape, 4), dtype=np.uint8)
        heatmap[..., 0] = (saliency_np * 255).astype(np.uint8)
        heatmap[..., 1] = (saliency_np * saliency_np * 200).astype(np.uint8)
        heatmap[..., 2] = 0
        heatmap[..., 3] = (saliency_np * 180).astype(np.uint8)

        # Composite onto original image
        heatmap_img = PILImage.fromarray(heatmap, "RGBA")
        base = image.convert("RGBA")
        overlay = PILImage.alpha_composite(base, heatmap_img)

        buf = io.BytesIO()
        overlay.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    async def generate_heatmap(self, image_bytes: bytes) -> bytes:
        """Async wrapper — runs inference in a thread to avoid blocking."""
        return await asyncio.to_thread(self._generate_heatmap, image_bytes)


gradcam_service = GradCAMService()
