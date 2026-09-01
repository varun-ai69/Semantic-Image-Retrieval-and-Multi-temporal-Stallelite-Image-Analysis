# Infrastructure & Containerization (`infra/`)

This directory contains container configurations and offline provisioning scripts for running the database, vector search, and storage stack on-premises.

## Running the Infrastructure

```bash
# Start all containers (Postgres/PostGIS, Qdrant, MinIO)
docker compose -f infra/docker-compose.yml up -d

# Stop all containers
docker compose -f infra/docker-compose.yml down

# Reset databases and re-run schema.sql & seed.sql fresh
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d
```

## Services Summary

- `eo_postgres`: PostgreSQL 16 with PostGIS 3.4 (`localhost:5434` -> `5432` internal). Automatically executes `backend/db/schema.sql` and `backend/db/seed.sql` on first launch.
- `eo_qdrant`: Qdrant Vector Search Engine (`localhost:6333` REST / `6334` gRPC).
- `eo_qdrant_init`: Python initializer that creates the `tile_embeddings` collection (512-dim Cosine) and payload indexes.
- `eo_minio`: S3-compatible local object storage for satellite imagery tiles (`localhost:9000` API / `localhost:9001` Web Console).

## Directory Structure

```
infra/
├── docker-compose.yml         # Container configuration
├── docker/                    # Staging folder for future app Dockerfiles
│   └── .gitkeep
└── scripts/
    ├── stage_offline_deps.sh  # Pre-download weights & datasets
    └── test_offline_mode.sh   # Offline compliance test
```
