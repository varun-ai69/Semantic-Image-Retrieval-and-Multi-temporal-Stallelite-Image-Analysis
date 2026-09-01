# ProjectContext.md
### Semantic Retrieval & Multi-Temporal Change Analysis of Satellite Imagery

**PS Number:** SIH-26227
**Title:** Semantic Retrieval and Multi-Temporal Change Analysis of Satellite Imagery
**Organization:** Ministry of Defence (MoD)
**Department:** Indian Army (DGIS)
**Category:** Software · **Theme:** Space Technology

This document is the single source of truth for the project — what's being asked, how we're solving it, every phase in detail, the database/metadata design, the final tech stack, and the repo layout. Anyone (or any tool) picking up this project cold should be able to read this file and understand the whole system.

---

## 1. What the organisation wants, and how we're approaching it

The Indian Army needs to search satellite/EO imagery archives **by meaning**, not just by coordinates and date, and needs the system to **automatically flag real changes** over time (construction, land clearance, water-extent change, road development) while filtering out false alarms caused by weather, season, sun angle, or misalignment. All of it must run **fully on-premises**, with the ability to add new imagery incrementally, and must remain operational with the network disabled.

Our approach in one sentence: **a trained vision-language encoder makes the archive searchable by meaning, a trained change-detection model precomputed at ingestion time makes "what changed" a fast lookup instead of a live computation, and a thin intent-routing agent sits in front of both so the analyst never needs to know which tool is running underneath.**

### 1.1 Requirement-by-requirement breakdown

| Section | What it asks | What we build |
|---|---|---|
| 2.2.1 | Search imagery by meaning (text or image), not just coordinates/date | Fine-tuned RemoteCLIP encoder turns text and images into comparable vectors; a vector DB finds nearest matches, filterable by AOI/date/sensor |
| 2.2.2 | For a place/time window, find real changes, classify them, and say when they first appeared | Change-detection model on co-registered before/after pairs; a classifier labels change type; backward time-walk finds earliest visible date |
| 2.2.3 | Don't call it change if it's weather/season/angle/misalignment | Cloud/shadow masking, radiometric normalization, sub-pixel co-registration before any comparison; a confidence score gates everything shown |
| 2.2.4 | Let the analyst find more places like one they found, without a new search | Tiles pre-clustered (HDBSCAN over embeddings); one click surfaces cluster members |
| 2.2.5 | Working analyst queue: evidence, confirm/reject, audit trail, exportable proof | Review-queue UI backed by a logged decisions table, feeding a reranker; full lineage carried into every export |
| 2.2.6 | Scale, incremental ingestion, fully on-prem | Vector DB with incremental upsert (no full reindex); PostGIS-backed metadata catalogue; entire stack in local Docker containers |
| 2.2.7 | Public/organiser imagery only; full demo with network disabled after setup | All weights/datasets staged locally beforehand; offline flags set in code; full pipeline rehearsed with network physically off |

---

## 2. Core architectural decisions (why the system is shaped this way)

- **Two pipelines.** Pipeline 1 (ingestion) runs once per new image batch, does all the heavy computation (embedding, change detection), and caches results. Pipeline 2 (query-time) runs on every analyst request and, in the common case, only ever does fast lookups against what Pipeline 1 already computed.
- **Three storage layers, each doing one job:**
  - **Vector DB** (Qdrant) — semantic embeddings only. Used for text-to-image search, image-to-image search, and discovery/clustering. **Never used for change detection.**
  - **Relational + spatial DB** (PostgreSQL + PostGIS) — tile registry, scene registry, precomputed change events, clusters, review queue, audit trail. All location/date lookups (including change detection) go through here using spatial SQL (`ST_Intersects` etc.), not vector similarity.
  - **File/object storage** — the actual raw image tile files. Vector DB and relational DB both only store a `file_path` pointer back to this, never the pixels themselves.
- **Training data vs. archive data are two separate worlds.** A small, captioned public+local dataset trains the encoder once. The archive (the actual searchable product) never needs captions — every tile is just pushed through the already-trained encoder automatically.
- **Change detection is precomputed wherever possible.** Every new tile is compared against its immediate predecessor at ingestion time and the result cached in `change_events`. This is what makes both "what changed at this specific AOI" and "show me anything that changed recently, anywhere" fast, table-driven queries instead of live model runs.
- **AOI resolution is grid-intersection based**, not a single big-image operation: an AOI polygon is intersected against the fixed tile grid to get a list of tiles, and each tile is resolved independently (nearest available date, cached-or-live change result, quality gate), then aggregated back to the analyst.

---

## 3. Phases (detailed)

### Phase 0 — Architecture lock-in & environment setup
- Finalize the three-storage-layer design (Section 2).
- Choose vector DB: **Qdrant** (simpler native payload-filtering than Milvus for this scope).
- Set up Docker Compose skeleton: Postgres+PostGIS, Qdrant, object storage (MinIO), placeholder API service.
- Set up `PROVENANCE.md` — every dataset/model logged with source, licence, checksum, date pulled, from day one.
- **Not schema, but decide:** tile size (512×512 recommended), overlap (10%), coordinate reference system for storage (EPSG:4326 for lat/long consistency across the DB; reproject per-scene on ingest).

### Phase 1 — Data staging (before network is disabled for good)
- **Training data (bucket 1 — captioned):** RSICD, RSITMD, UCM-Captions (retrieval); a small (few hundred) hand-captioned local set for domain vocabulary fit.
- **Training data (bucket 2 — change labels):** LEVIR-CD, OSCD, S2Looking, xView2.
- **Archive data (bucket 3 — no captions needed):** the actual AOI imagery — Sentinel-2 COGs over the target region, multi-year (3-5+ years ideally, to have real change to find).
- Log every dataset in `PROVENANCE.md`: name, source URL, licence, checksum, date pulled.

### Phase 2 — Preprocessing pipeline
Runs on every incoming scene, before anything else touches it.
1. **Validate & reproject** — check CRS/nodata, reproject to common CRS (`rasterio.warp`).
2. **Tile** — cut into fixed 512×512 patches with 10% overlap; assign stable `tile_id`; store `geometry` (footprint polygon).
3. **Quality masking** — cloud/shadow/haze detection (`s2cloudless`); tiles above a cloud threshold flagged low-quality.
4. **Radiometric normalization** — histogram matching (`skimage.exposure.match_histograms`) to reduce seasonal/illumination/sensor differences.
5. **Co-registration** — sub-pixel alignment against overlapping historical tiles (`AROSICS`).
6. **Compute `quality_confidence`** — single combined score from cloud %, registration residual, and seasonal delta; gates every downstream step.
- **Output:** populated `tiles` table (Section 4.2), clean tile files in storage.

### Phase 3 — Retrieval encoder training (one-time)
- Load RemoteCLIP (ViT-B/32) pretrained weights via `open_clip`.
- Fine-tune on bucket-1 captioned data (contrastive/InfoNCE loss, low LR, freeze most of the backbone, fine-tune last blocks + projection heads).
- Evaluate with Recall@1/5/10 on a held-out split.
- Freeze the resulting checkpoint; tag it with an `embedding_version` string — every tile embedded downstream records which version produced its vector.

### Phase 4 — Embed the archive + populate the vector DB
- Run **every** archive tile through the trained encoder once (no captions involved — see Section 2).
- Upsert `{vector, payload}` into the Qdrant `tile_embeddings` collection (Section 4.1).
- Build the **incremental ingestion script**: this is the exact "add a new region" path — new tiles → preprocessing (Phase 2) → encoder (Phase 3 model) → upsert. No full reindex, ever.

### Phase 5 — Change detection model training + ingestion-time inference (one-time training, ongoing inference)
- Fine-tune a Siamese/BIT-style model (via the Open-CD toolbox) on bucket-2 data (LEVIR-CD + OSCD + S2Looking).
- Add a lightweight change-type classifier on top (construction / clearance / water / road / other), fine-tuned on xView2 + local examples.
- **At every ingestion event:** run this model on the new tile vs. its immediate predecessor at the same location; write the result to `change_events`.
- Implement the **backward walk**: for a confirmed change, step backward through the tile's time series (gated by `quality_confidence`) to find `earliest_visible_date`.

### Phase 6 — On-demand change resolution (AOI / arbitrary date-range logic)
This is the service that answers "what changed here between date A and date B," handling AOIs that span many tiles:
1. Spatial intersect: `SELECT tile_id FROM tiles WHERE ST_Intersects(geometry, :aoi_polygon)`.
2. For each returned tile independently: find the image closest to date A and closest to date B (within a tolerance window, e.g. ±3 months), respecting `quality_confidence`. If nothing usable exists near a requested date, mark `insufficient_coverage`.
3. Check `change_events` for that exact tile pair — reuse if cached; otherwise run the Phase 5 model live on just that pair, then cache the result.
4. Aggregate all per-tile results and return as a list (map markers + review-queue-style rows), not one blended answer.
- Build this as a standalone, independently testable function — it's called by the query-time agent (Phase 8) but should be unit-testable on its own.

### Phase 7 — Discovery / clustering
- Batch job (not per-query): run HDBSCAN over the vector DB's embeddings.
- Write `cluster_id` back onto each tile (in both the relational DB and the vector DB payload).
- Re-run periodically as new tiles are ingested (not synchronously per-request).

### Phase 8 — Query-time agent (intent router)
- Classifies analyst input into: `semantic_search`, `change_query`, `similarity_discovery`, `queue_query` / `export_action`.
- Dispatches to exactly the tool(s) needed — no step here re-runs Phase 3/5 training, only inference/lookups (and only Phase 6's live-compute fallback in the rare uncached case).
- Simplest reliable implementation: a small rules/keyword+parameter-extraction classifier is enough for v1; an LLM-based classifier is a drop-in upgrade later if needed — architecture doesn't change either way.

### Phase 9 — Backend API
- REST endpoints: `/search` (text/image), `/change` (AOI polygon + date range body), `/discover/{tile_id}`, `/queue`, `/export`.
- Wraps the Phase 4/6/7 services; owns the quality filter + reranker step before returning results.

### Phase 10 — Frontend (Leaflet)
- Full-globe base map (Leaflet + `titiler`-served COG tiles for your own archive imagery, OSM/base layer for context).
- **AOI drawing** — `Leaflet.draw` or `Leaflet-Geoman` plugin, outputs GeoJSON directly compatible with the backend's `ST_Intersects` query.
- **Pin-point mode** — click-to-drop-marker as a lighter alternative to drawing a full polygon; internally becomes a small buffered point fed into the same Phase 6 logic.
- Search bar (text + image upload) → results grid.
- Location detail view — before/after slider, timeline, confidence, change type.
- Review queue view — confirm/reject buttons.
- Cluster/"find similar" map view.

### Phase 11 — Review, feedback, provenance, export
- Confirm/reject writes to `review_items` (Section 4.2).
- Reranker combines similarity score + change confidence + analyst feedback history (start simple: logistic regression or hand-weighted scoring; upgrade later).
- Every export (CSV/GeoJSON/PDF) carries `scene_id`, `model_version`, `confidence`, and the analyst's decision.

### Phase 12 — Offline packaging & rehearsal
- Stage all model weights and datasets locally; set offline env flags (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).
- `docker-compose.yml` bundles everything — Postgres+PostGIS, Qdrant, MinIO, titiler, backend, frontend — built and vendored locally.
- **Test the entire stack with network physically disabled** well before the actual demo.

### Phase 13 — Evaluation harness
- Retrieval: Precision@k, Recall@k, nDCG against held-out query/relevance judgements.
- Change detection: Precision/Recall/F1, broken down by change type.
- System: indexed area, tile/scene count, index build time, incremental ingestion time, storage footprint, p50/p95 query latency, hardware used — all logged automatically by a benchmark script, not hand-measured.

---

## 4. Database & metadata design (not final, but the working baseline)

### 4.1 Vector DB — one Qdrant collection

```
Collection: tile_embeddings
  id:      tile_id
  vector:  float[512 or 768]        # output of the trained encoder (Phase 3/4)
  payload:
    geometry:            GeoJSON polygon (tile footprint)
    centroid_lat:          float
    centroid_lon:          float
    acquisition_date:      date
    sensor:                 string
    quality_confidence:     float (0-1)
    cluster_id:             string (nullable, filled by Phase 7)
    scene_id:               string
```

### 4.2 Relational + spatial DB (PostgreSQL + PostGIS)

```sql
CREATE TABLE scenes (
  scene_id         TEXT PRIMARY KEY,
  source            TEXT,
  acquisition_date  TIMESTAMP,
  crs               TEXT,
  footprint         GEOMETRY(Polygon, 4326),
  ingested_at       TIMESTAMP DEFAULT now(),
  raw_file_path     TEXT,
  provenance        JSONB
);

CREATE TABLE tiles (
  tile_id                TEXT PRIMARY KEY,
  scene_id                TEXT REFERENCES scenes(scene_id),
  geometry                GEOMETRY(Polygon, 4326),
  acquisition_date         TIMESTAMP,
  sensor                    TEXT,
  cloud_pct                 FLOAT,
  registration_residual      FLOAT,
  quality_confidence         FLOAT,
  file_path                   TEXT,
  embedding_version           TEXT,
  cluster_id                   TEXT,
  created_at                    TIMESTAMP DEFAULT now()
);
CREATE INDEX tiles_geom_idx ON tiles USING GIST (geometry);
CREATE INDEX tiles_date_idx ON tiles (acquisition_date);

CREATE TABLE change_events (
  event_id                 SERIAL PRIMARY KEY,
  location_key               TEXT,
  tile_before                  TEXT REFERENCES tiles(tile_id),
  tile_after                    TEXT REFERENCES tiles(tile_id),
  change_type                    TEXT,
  confidence                      FLOAT,
  earliest_visible_date             TIMESTAMP,
  detected_date                      TIMESTAMP DEFAULT now(),
  model_version                       TEXT,
  quality_flag                         TEXT   -- ok / insufficient_coverage / low_confidence
);
CREATE INDEX change_events_date_idx ON change_events (detected_date);
CREATE INDEX change_events_conf_idx ON change_events (confidence);

CREATE TABLE clusters (
  cluster_id    TEXT PRIMARY KEY,
  label          TEXT,
  computed_at     TIMESTAMP DEFAULT now(),
  model_version    TEXT
);

CREATE TABLE review_items (
  item_id       SERIAL PRIMARY KEY,
  event_id       INT REFERENCES change_events(event_id) NULL,
  tile_id         TEXT REFERENCES tiles(tile_id) NULL,
  rank_score       FLOAT,
  status             TEXT DEFAULT 'pending',
  analyst_id           TEXT,
  decided_at             TIMESTAMP,
  query_context            JSONB
);

CREATE TABLE exports (
  export_id      SERIAL PRIMARY KEY,
  requested_by    TEXT,
  requested_at     TIMESTAMP DEFAULT now(),
  item_ids           INT[],
  format               TEXT,
  file_path             TEXT
);
```

### 4.3 File / object storage

```
/data/tiles/{year}/{tile_id}.tif
/data/scenes/{scene_id}.tif      (optional, keep full scenes too)
```

### 4.4 Metadata that must travel with every tile

| Field | Why |
|---|---|
| `tile_id` | Stable identity, referenced everywhere |
| `scene_id` | Traces back to source scene |
| `geometry` | Spatial filtering, AOI intersection |
| `centroid_lat` / `centroid_lon` | Fast map plotting |
| `acquisition_date` | Time filtering, change-pair matching |
| `sensor` | Filter, cross-sensor normalization |
| `cloud_pct` | Quality gating |
| `registration_residual` | Quality gating (alignment) |
| `quality_confidence` | Combined gate used everywhere downstream |
| `embedding_version` | Which encoder checkpoint produced the vector |
| `file_path` | Where the actual image lives |
| `provenance` | Licence, source URL — required submission deliverable |
| `ingested_at` | Audit trail |

---

## 5. Tech stack (final)

| Layer | Choice | Why |
|---|---|---|
| Preprocessing | `rasterio`, `s2cloudless`, `AROSICS`, `scikit-image` | Standard, well-supported EO preprocessing tooling |
| Retrieval model | RemoteCLIP (via `open_clip`), fine-tuned | Open weights, state-of-the-art on remote sensing retrieval benchmarks |
| Change detection model | Siamese/BIT via Open-CD toolbox | Ready-made implementations, easy to fine-tune on LEVIR-CD/OSCD/S2Looking |
| Clustering | HDBSCAN (`scikit-learn`/`hdbscan`) | No need to pick k, handles uneven density |
| Vector DB | Qdrant | Native payload filtering + incremental upsert, simple to self-host |
| Relational + spatial DB | PostgreSQL + PostGIS | Industry-standard spatial querying (`ST_Intersects` etc.) |
| Object/file storage | Local filesystem, or MinIO if S3-style access is wanted | Fully on-prem, no cloud dependency |
| Tile serving (map layer) | `titiler` | Serves your own COGs as map tiles locally |
| Backend API | Python, FastAPI | Async-friendly, fast to iterate, plays well with the ML stack |
| ORM / migrations | SQLAlchemy + Alembic | Standard, works cleanly with PostGIS |
| Frontend | React + Leaflet | Leaflet is the standard open-source mapping library; React for the app shell |
| AOI drawing | `Leaflet.draw` / `Leaflet-Geoman` | Outputs GeoJSON directly, matches backend's spatial queries |
| Styling | Tailwind CSS | Fast to build a clean analyst UI |
| Containerization | Docker + Docker Compose | Required for the fully on-prem, offline demo constraint |
| Background/async jobs (ingestion) | Celery + Redis (optional, if ingestion needs to be async) | Keeps heavy embedding/change-model inference off the request path |
| Evaluation/benchmark scripts | Python, `pytest` for correctness, custom scripts for metrics/latency logging | Needed for the required reproducible evaluation report |

---

## 6. Repo file structure (baseline)

```
project-root/
├── README.md
├── docker-compose.yml
├── .env.example
├── PROVENANCE.md
├── docs/
│   ├── ProjectContext.md              # this file
│   ├── architecture-note.md
│   └── evaluation-report.md
├── data/                              # gitignored — local data staging
│   ├── raw/
│   ├── tiles/
│   └── training/
├── models/                            # gitignored/LFS — local weights only
│   ├── retrieval/
│   └── change_detection/
├── backend/
│   ├── api/                           # FastAPI app
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── search.py
│   │   │   ├── change.py
│   │   │   ├── discovery.py
│   │   │   └── queue.py
│   │   ├── agent/
│   │   │   ├── intent_router.py       # Phase 8
│   │   │   └── tools/
│   │   │       ├── vector_search.py
│   │   │       ├── spatial_lookup.py
│   │   │       ├── change_resolver.py # Phase 6 logic
│   │   │       └── cluster_lookup.py
│   │   ├── db/
│   │   │   ├── models.py              # SQLAlchemy models matching Section 4.2
│   │   │   ├── session.py
│   │   │   └── migrations/            # Alembic
│   │   └── services/
│   │       ├── vector_store.py        # Qdrant client wrapper
│   │       ├── reranker.py
│   │       └── quality_filter.py
│   ├── ingestion/
│   │   ├── preprocess.py              # Phase 2
│   │   ├── embed_and_store.py         # Phase 4
│   │   ├── change_detect.py           # Phase 5 (ingestion-time inference)
│   │   └── cluster.py                 # Phase 7
│   ├── training/
│   │   ├── train_retrieval_encoder.py # Phase 3
│   │   ├── train_change_model.py      # Phase 5 (training)
│   │   └── datasets/
│   ├── evaluation/
│   │   ├── retrieval_eval.py
│   │   ├── change_eval.py
│   │   └── benchmark.py               # Phase 13
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView.jsx
│   │   │   ├── AOIDrawTool.jsx
│   │   │   ├── PinPointTool.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   ├── ResultsGrid.jsx
│   │   │   ├── LocationDetail.jsx
│   │   │   ├── ReviewQueue.jsx
│   │   │   └── ClusterMapView.jsx
│   │   ├── pages/
│   │   ├── api/                       # backend API client calls
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
└── infra/
    ├── docker/
    │   ├── backend.Dockerfile
    │   ├── frontend.Dockerfile
    │   └── titiler.Dockerfile
    └── scripts/
        ├── stage_offline_deps.sh      # Phase 1/12 — pull everything before network cutoff
        └── test_offline_mode.sh       # Phase 12 — rehearsal with network disabled
```

---

## 7. Status note

This document reflects the design as discussed and worked out through planning conversations — **schema fields, table names, and folder layout are the working baseline, not finalized/frozen.** Expect adjustments once implementation starts (e.g. tile size trade-offs, whether per-tile change masks are stored for a future heatmap overlay, exact intent-router implementation). Update this file as decisions firm up so it stays the single source of truth.
