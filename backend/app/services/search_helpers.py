"""Helper functions for building Qdrant search filters."""

from typing import Optional

from qdrant_client.models import Filter, FieldCondition, MatchValue


def build_qdrant_filter(
    diagnosis: Optional[str] = None,
    tissue_type: Optional[str] = None,
    benign_malignant: Optional[str] = None,
) -> Optional[Filter]:
    """Build a Qdrant filter from optional query parameters."""
    conditions = []
    if diagnosis:
        conditions.append(
            FieldCondition(key="diagnosis", match=MatchValue(value=diagnosis))
        )
    if tissue_type:
        conditions.append(
            FieldCondition(key="tissue_type", match=MatchValue(value=tissue_type))
        )
    if benign_malignant:
        conditions.append(
            FieldCondition(
                key="benign_malignant", match=MatchValue(value=benign_malignant)
            )
        )
    if conditions:
        return Filter(must=conditions)
    return None
