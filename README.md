# Semantic Retrieval & Multi-Temporal Change Analysis of Satellite Imagery

> **Problem Statement Number:** SIH-26227  
> **Organization:** Ministry of Defence (MoD) — Indian Army (DGIS)  
> **Category:** Software | **Theme:** Space Technology  
> **Repository:** [`varun-ai69/Semantic-Image-Retrieval-and-Multi-temporal-Stallelite-Image-Analysis`](https://github.com/varun-ai69/Semantic-Image-Retrieval-and-Multi-temporal-Stallelite-Image-Analysis)

---

## 📌 Executive Summary

Modern defense analysts require the capability to query satellite imagery archives **by semantic meaning** (e.g. *"find airstrips with visible hangars near river bends"*) rather than relying strictly on geographic coordinates or metadata dates. Additionally, the system must automatically flag **true multi-temporal changes** (such as new construction, land clearance, road development, or water-extent shifts) while suppressing false alarms caused by cloud coverage, seasonal variations, sun angles, or spatial misalignment.

This platform provides an end-to-end, **100% on-premises, network-isolated solution** utilizing fine-tuned RemoteCLIP vision-language encoders, Qdrant vector indexing, PostGIS spatial caching, Siamese/BIT change detection, and a unified intent-routing agent.

---

## 🏗️ System Architecture & Storage Strategy

The system enforces a strict separation between ingestion-time heavy precomputation and query-time rapid resolution:

```
                            +---------------------------------+
                            |   Analyst Web Application UI    |
                            |   (React + Leaflet + Geoman)    |
                            +----------------+----------------+
                                             | REST (/api/v1/...)
                            +----------------v----------------+
                            |     FastAPI Backend Service     |
                            |      Intent Router Agent        |
                            +----+-----------+-----------+----+
                                 |           |           |
            +--------------------+           |           +--------------------+
            | Vector Queries                 | Spatial SQL Queries            | Tile Streaming
    +-------v-------+                +-------v-------+                +-------v-------+
    |   Qdrant DB   |                |  PostgreSQL / |                |  Local Files /|
    | (Embeddings & |                |    PostGIS    |                | TiTiler COGs  |
    |  Clusters)    |                | (Meta & Cache)|                | MinIO Storage |
    +---------------+                +---------------+                +---------------+
```

### Three Storage Layers
1. **Vector DB (Qdrant)**: Stores 512-dim RemoteCLIP embeddings for text-to-image search, image-to-image search, and HDBSCAN cluster IDs.
2. **Relational & Spatial DB (PostgreSQL + PostGIS)**: Stores scene/tile metadata, spatial boundaries (`GEOMETRY(Polygon, 4326)`), precomputed change events, analyst review decisions, and export audit logs.
3. **File/Object Storage (MinIO / Local)**: Holds raw Earth Observation imagery and preprocessed Cloud-Optimized GeoTIFFs (COGs).

---

## 📁 Repository Directory Structure

```
.
├── ProjectContext.md                       # Single source of truth for project requirements & schema
├── README.md                               # Primary project guide & repository documentation
├── PROVENANCE.md                           # Data & model provenance tracking audit log
├── .env.example                            # Configuration environment variables template
├── docs/                                   # Architectural notes & evaluation benchmark harness reports
├── data/                                   # Git-ignored data staging (raw imagery, 512x512 tiles, training sets)
├── models/                                 # Git-ignored local model weights (RemoteCLIP, Change Detection)
├── backend/                                # Python FastAPI services, ingestion scripts, & ML models
│   ├── api/                                # REST API routers & Intent Routing Agent
│   │   ├── routers/                        # Endpoints (/api/v1/search, /change, /discover, /queue, /export)
│   │   └── agent/                          # Query classifier & tools (vector search, spatial lookup, change resolver)
│   ├── db/                                 # PostGIS SQLAlchemy models, schema.sql, seed.sql, vector_schema.py
│   ├── services/                           # Qdrant client wrapper, analyst reranker, quality filtering
│   ├── ingestion/                          # Preprocessing, cloud masking, co-registration, embedding & change inference
│   ├── training/                           # Offline fine-tuning scripts (RemoteCLIP & Siamese change models)
│   └── evaluation/                         # Automated precision/recall/F1 & latency benchmarking suite
├── frontend/                               # React + Vite + Leaflet mapping web application
│   └── src/
│       ├── components/                     # MapView, AOIDrawTool, SearchBar, ResultsGrid, ReviewQueue, LocationDetail
│       ├── pages/                          # Intelligence dashboard & analyst workspace views
│       └── api/                            # REST API client layer
└── infra/                                  # Infrastructure docker-compose & offline staging scripts
    ├── docker-compose.yml                  # Container orchestration for PostGIS, Qdrant, MinIO
    ├── docker/                             # Placeholder directory for application Dockerfiles
    └── scripts/                            # Offline dependency staging & network-isolated testing scripts
```

---

## 🔌 API Route Specification (`/api/v1`)

All backend services are version-controlled under the `/api/v1` base route prefix:

| Endpoint | Method | Input | Description |
|---|---|---|---|
| `/api/v1/search` | `POST` | Text query or image file | Performs semantic vector similarity search via Qdrant & RemoteCLIP |
| `/api/v1/change` | `POST` | AOI GeoJSON + Date Range | Evaluates spatial tile intersections & fetches precomputed/live change events |
| `/api/v1/discover/{tile_id}` | `GET` | `tile_id` string | Retrieves pre-clustered HDBSCAN tile members for discovery |
| `/api/v1/queue` | `GET / POST` | Analyst Decision payload | Manages review queue items and logs confirm/reject decisions |
| `/api/v1/export` | `POST` | Export format + item IDs | Generates exportable evidence reports carrying full provenance lineage |

---

## ⚡ Quickstart Guide (Local Infrastructure)

### 1. Environment Preparation
```bash
# Clone the repository
git clone https://github.com/varun-ai69/Semantic-Image-Retrieval-and-Multi-temporal-Stallelite-Image-Analysis.git
cd Semantic-Image-Retrieval-and-Multi-temporal-Stallelite-Image-Analysis

# Initialize environment variables
cp .env.example .env
```

### 2. Launch Local Database & Vector Containers
```bash
docker compose -f infra/docker-compose.yml up -d
```

### 3. Service Access Endpoints
- **PostgreSQL / PostGIS**: `localhost:5434` (database: `eo_archive`, user: `eo_admin`, password: `eo_password`)
- **Qdrant Vector DB REST API**: `http://localhost:6333`
- **Qdrant Vector Dashboard**: `http://localhost:6333/dashboard`
- **MinIO Object Storage S3 API**: `http://localhost:9000`
- **MinIO Web Console**: `http://localhost:9001` (user: `eo_admin`, password: `eo_password`)

---

## 🛡️ Offline & On-Premises Compliance

This repository is built for **air-gapped deployment**:
- Model weights and datasets are pre-staged in `models/` and `data/` using `infra/scripts/stage_offline_deps.sh`.
- Code sets strict offline flags (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).
- All execution is validated via `infra/scripts/test_offline_mode.sh` with network interfaces physically disabled.

---

## 📄 License & Provenance
Logged in [`PROVENANCE.md`](PROVENANCE.md) per Ministry of Defence submission requirements.
