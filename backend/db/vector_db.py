"""
vector_db.py
Vector DB schema and payload validation models for Qdrant collection `tile_embeddings`.
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PayloadSchemaType,
    PointStruct,
)

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "tile_embeddings")
EMBEDDING_DIM = 512

# ============================================================
# 1. Pydantic Payload Schema Validation
# ============================================================

class TileVectorPayload(BaseModel):
    """Validation schema for metadata payload stored with each vector in Qdrant."""
    tile_id: str = Field(..., description="Unique tile ID matching Postgres tiles.tile_id")
    scene_id: Optional[str] = Field(None, description="Links to Postgres scenes.scene_id")
    site_key: Optional[str] = Field(None, description="Stable location identifier across time")
    centroid_lat: Optional[float] = Field(None, description="Latitude centroid")
    centroid_lon: Optional[float] = Field(None, description="Longitude centroid")
    acquisition_date: Optional[int] = Field(None, description="UNIX timestamp in seconds for range filtering")
    sensor: Optional[str] = Field(None, description="Satellite sensor name (e.g. sentinel2)")
    quality_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Combined quality gate (0-1)")
    cluster_id: Optional[str] = Field(None, description="HDBSCAN cluster ID or null")
    embedding_version: Optional[str] = Field(None, description="Encoder model version tag")

    class Config:
        extra = "allow"


class TileVectorPoint(BaseModel):
    """Validation schema for inserting a vector point into Qdrant."""
    id: int | str
    vector: List[float] = Field(..., description="512-dimensional embedding vector")
    payload: TileVectorPayload

    def validate_dim(self) -> bool:
        return len(self.vector) == EMBEDDING_DIM


# ============================================================
# 2. Qdrant Collection & Index Schema Initializer
# ============================================================

def init_qdrant_schema(client: Optional[QdrantClient] = None):
    if client is None:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # 1. Create collection if not exists
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"Created collection '{COLLECTION_NAME}' (dim={EMBEDDING_DIM}, cosine distance).")

    # 2. Create payload indexes for fast filtering
    indexes = [
        ("scene_id", PayloadSchemaType.KEYWORD),
        ("site_key", PayloadSchemaType.KEYWORD),
        ("sensor", PayloadSchemaType.KEYWORD),
        ("cluster_id", PayloadSchemaType.KEYWORD),
        ("embedding_version", PayloadSchemaType.KEYWORD),
        ("acquisition_date", PayloadSchemaType.INTEGER),
        ("quality_confidence", PayloadSchemaType.FLOAT),
    ]
    for field_name, schema_type in indexes:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=schema_type,
        )
    print(f"Verified {len(indexes)} payload indexes on '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    init_qdrant_schema()
