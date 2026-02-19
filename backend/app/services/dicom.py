"""
DICOM file parsing service.

Extracts pixel data and metadata from DICOM files (.dcm) for use
with the similarity search pipeline. Supports standard DICOM tags
for medical imaging metadata.
"""

import io
from typing import Optional

import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
from PIL import Image
import numpy as np

from app.core.logging_config import logger


class DicomService:
    """Parses DICOM files and extracts images + metadata."""

    def extract_image(self, dicom_bytes: bytes) -> bytes:
        """Extract pixel data from DICOM and return as JPEG bytes."""
        ds = pydicom.dcmread(io.BytesIO(dicom_bytes))

        # Apply VOI LUT for proper windowing
        pixel_array = apply_voi_lut(ds.pixel_array, ds)

        # Handle photometric interpretation
        if ds.PhotometricInterpretation == "MONOCHROME1":
            pixel_array = np.max(pixel_array) - pixel_array

        # Normalize to 8-bit
        pixel_array = pixel_array.astype(float)
        pixel_array = ((pixel_array - pixel_array.min()) /
                       (pixel_array.max() - pixel_array.min() + 1e-8) * 255)
        pixel_array = pixel_array.astype(np.uint8)

        # Convert to PIL Image
        if len(pixel_array.shape) == 2:
            image = Image.fromarray(pixel_array, mode="L").convert("RGB")
        else:
            image = Image.fromarray(pixel_array, mode="RGB")

        # Save as JPEG bytes
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=95)
        buf.seek(0)
        return buf.getvalue()

    def extract_metadata(self, dicom_bytes: bytes) -> dict:
        """Extract relevant metadata from DICOM headers."""
        ds = pydicom.dcmread(io.BytesIO(dicom_bytes))

        def safe_get(tag: str) -> Optional[str]:
            val = getattr(ds, tag, None)
            return str(val) if val is not None else None

        return {
            "patient_age": safe_get("PatientAge"),
            "patient_sex": safe_get("PatientSex"),
            "body_part": safe_get("BodyPartExamined"),
            "modality": safe_get("Modality"),
            "study_description": safe_get("StudyDescription"),
            "series_description": safe_get("SeriesDescription"),
            "institution": safe_get("InstitutionName"),
            "manufacturer": safe_get("Manufacturer"),
            "rows": getattr(ds, "Rows", None),
            "columns": getattr(ds, "Columns", None),
        }


dicom_service = DicomService()
