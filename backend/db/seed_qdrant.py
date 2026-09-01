"""
seed_qdrant.py
Populates Qdrant tile_embeddings collection with sample 512-dim vectors
and metadata payloads corresponding to the demo tiles seeded in PostgreSQL.
"""

import os
import random
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "tile_embeddings")

# Fixed random seed so vector values are deterministic across runs
random.seed(42)

def generate_unit_vector(dim=512):
    vec = [random.gauss(0, 1) for _ in range(dim)]
    norm = sum(x**2 for x in vec) ** 0.5
    return [x / norm for x in vec]

DEMO_POINTS = [
    PointStruct(
        id=1,
        vector=generate_unit_vector(512),
        payload={
            "tile_id": "tile_demo_A_2021",
            "scene_id": "scene_demo_2021",
            "site_key": "site_23.0225_72.5714",
            "centroid_lat": 23.0275,
            "centroid_lon": 72.5764,
            "acquisition_date": 1615354200,  # 2021-03-10
            "sensor": "sentinel2",
            "quality_confidence": 0.93,
            "cluster_id": "cluster_industrial_01",
            "embedding_version": "remoteclip_v1",
        }
    ),
    PointStruct(
        id=2,
        vector=generate_unit_vector(512),
        payload={
            "tile_id": "tile_demo_A_2024",
            "scene_id": "scene_demo_2024",
            "site_key": "site_23.0225_72.5714",
            "centroid_lat": 23.0275,
            "centroid_lon": 72.5764,
            "acquisition_date": 1710221400,  # 2024-03-12
            "sensor": "sentinel2",
            "quality_confidence": 0.89,
            "cluster_id": "cluster_industrial_01",
            "embedding_version": "remoteclip_v1",
        }
    ),
    PointStruct(
        id=3,
        vector=generate_unit_vector(512),
        payload={
            "tile_id": "tile_demo_B_2024",
            "scene_id": "scene_demo_2024",
            "site_key": "site_23.0300_72.5850",
            "centroid_lat": 23.0300,
            "centroid_lon": 72.5850,
            "acquisition_date": 1710221400,  # 2024-03-12
            "sensor": "sentinel2",
            "quality_confidence": 0.91,
            "cluster_id": "cluster_industrial_01",
            "embedding_version": "remoteclip_v1",
        }
    ),
    PointStruct(
        id=4,
        vector=generate_unit_vector(512),
        payload={
            "tile_id": "tile_demo_C_2024_cloudy",
            "scene_id": "scene_demo_2024",
            "site_key": "site_23.0400_72.5600",
            "centroid_lat": 23.0400,
            "centroid_lon": 72.5600,
            "acquisition_date": 1710221400,  # 2024-03-12
            "sensor": "sentinel2",
            "quality_confidence": 0.21,
            "cluster_id": None,
            "embedding_version": "remoteclip_v1",
        }
    )
]

def main():
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Upsert the demo points
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=DEMO_POINTS,
    )
    print(f"Successfully seeded {len(DEMO_POINTS)} vector points into collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    main()
