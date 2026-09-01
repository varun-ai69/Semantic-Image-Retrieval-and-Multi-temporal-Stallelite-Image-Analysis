"""
vector_schema.py
Final Qdrant collection schema for tile embeddings.

Qdrant has no .sql-style schema file — a collection (and its payload
indexes) is created via client code, run once. This script IS the schema:
run it once against a fresh Qdrant instance and the collection is ready.
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PayloadSchemaType,
)

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "tile_embeddings")

# Must match the retrieval encoder's actual output dimension:
#   RemoteCLIP ViT-B/32  -> 512
#   RemoteCLIP ViT-L/14  -> 768
EMBEDDING_DIM = 512


def create_collection(client: QdrantClient):
    """
    Payload field reference:
      tile_id             keyword   - same as the Postgres tiles.tile_id
      scene_id             keyword   - links back to Postgres scenes.scene_id
      site_key              keyword   - same physical spot across dates
      centroid_lat            float    - also stored as a Qdrant geo point
      centroid_lon              float
      acquisition_date            integer  - UNIX timestamp (seconds).
      sensor                        keyword
      quality_confidence              float   - 0-1, used to downrank/exclude low-quality tiles
      cluster_id                        keyword | null
      embedding_version                    keyword
    """
    if client.collection_exists(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' already exists — skipping creation.")
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )
    print(f"Created collection '{COLLECTION_NAME}' (dim={EMBEDDING_DIM}, cosine distance).")


def create_payload_indexes(client: QdrantClient):
    """
    Payload indexes enable high-speed filtered search (AOI/date/sensor
    combined with vector similarity) instead of a full scan.
    """
    indexes = [
        ("scene_id", PayloadSchemaType.KEYWORD),
        ("site_key", PayloadSchemaType.KEYWORD),
        ("sensor", PayloadSchemaType.KEYWORD),
        ("cluster_id", PayloadSchemaType.KEYWORD),
        ("embedding_version", PayloadSchemaType.KEYWORD),
        ("acquisition_date", PayloadSchemaType.INTEGER),   # enables date-range filters
        ("quality_confidence", PayloadSchemaType.FLOAT),    # enables quality-gate filters
    ]
    for field_name, schema_type in indexes:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=schema_type,
        )
    print(f"Created {len(indexes)} payload indexes on '{COLLECTION_NAME}'.")


def main():
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    create_collection(client)
    create_payload_indexes(client)
    print("Qdrant schema setup completed successfully.")


if __name__ == "__main__":
    main()
