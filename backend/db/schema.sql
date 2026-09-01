-- schema.sql
-- Consolidated schema — Semantic Retrieval & Multi-Temporal Change
-- Analysis of Satellite Imagery (PS-227 / SIH-26227)
--
-- Covers tables: scenes, tiles, change_events, clusters,
-- review_items, exports, search_log, ingestion_coverage.

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- 1. SCENES — one row per raw satellite download (before tiling)
-- ============================================================
CREATE TABLE IF NOT EXISTS scenes (
  scene_id          TEXT PRIMARY KEY,
  source            TEXT,                          -- 'sentinel2', 'bhoonidhi', etc.
  acquisition_date  TIMESTAMP,                      -- when the satellite captured it
  crs               TEXT,                           -- coordinate system of the raw file
  footprint         GEOMETRY(Polygon, 4326),        -- big polygon, whole-scene coverage
  ingested_at       TIMESTAMP DEFAULT now(),         -- when processed
  raw_file_path     TEXT,
  provenance        JSONB                           -- licence, source URL, original product ID
);

-- ============================================================
-- 2. TILES — one row per 512x512 crop, cut from a scene
-- ============================================================
CREATE TABLE IF NOT EXISTS tiles (
  tile_id                TEXT PRIMARY KEY,
  scene_id                TEXT REFERENCES scenes(scene_id),
  site_key                TEXT,                     -- stable ID for physical location across time
  geometry                GEOMETRY(Polygon, 4326),   -- tile footprint polygon
  centroid_lat             FLOAT,
  centroid_lon             FLOAT,
  acquisition_date         TIMESTAMP,
  sensor                    TEXT,
  cloud_pct                 FLOAT,                    -- 0-1, from cloud masking
  registration_residual      FLOAT,                    -- sub-pixel alignment residual (AROSICS)
  quality_confidence          FLOAT,                    -- combined quality score (0-1)
  embedding_version            TEXT,                     -- encoder version used
  cluster_id                     TEXT,                   -- HDBSCAN cluster ID
  band_count                       INT DEFAULT 4,
  bit_depth                        INT DEFAULT 16,
  file_size_bytes                  BIGINT,
  file_path                            TEXT,               -- main GeoTIFF
  thumbnail_path                        TEXT,               -- preview image
  created_at                              TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS tiles_geom_idx ON tiles USING GIST (geometry);
CREATE INDEX IF NOT EXISTS tiles_date_idx ON tiles (acquisition_date);
CREATE INDEX IF NOT EXISTS tiles_site_idx ON tiles (site_key);
CREATE INDEX IF NOT EXISTS tiles_cluster_idx ON tiles (cluster_id);

-- ============================================================
-- 3. CHANGE_EVENTS — output of comparing tile_before vs tile_after
-- ============================================================
CREATE TABLE IF NOT EXISTS change_events (
  event_id                SERIAL PRIMARY KEY,
  site_key                 TEXT,
  tile_before               TEXT REFERENCES tiles(tile_id),
  tile_after                 TEXT REFERENCES tiles(tile_id),
  change_type                 TEXT,      -- construction / clearance / water / road / other
  confidence                   FLOAT,     -- 0-1 confidence score
  earliest_visible_date         TIMESTAMP, -- backward time-walk earliest visible date
  detected_date                  TIMESTAMP DEFAULT now(),
  model_version                   TEXT,
  quality_flag                     TEXT   -- 'ok' / 'insufficient_coverage' / 'low_confidence'
);

CREATE INDEX IF NOT EXISTS change_events_site_idx ON change_events (site_key);
CREATE INDEX IF NOT EXISTS change_events_date_idx ON change_events (detected_date);
CREATE INDEX IF NOT EXISTS change_events_conf_idx ON change_events (confidence);

-- ============================================================
-- 4. CLUSTERS — groups discovered by HDBSCAN over embeddings
-- ============================================================
CREATE TABLE IF NOT EXISTS clusters (
  cluster_id     TEXT PRIMARY KEY,
  label           TEXT,
  computed_at      TIMESTAMP DEFAULT now(),
  model_version     TEXT
);

-- ============================================================
-- 5. REVIEW_ITEMS — analyst queue and audit trail
-- ============================================================
CREATE TABLE IF NOT EXISTS review_items (
  item_id       SERIAL PRIMARY KEY,
  event_id       INT REFERENCES change_events(event_id),
  tile_id         TEXT REFERENCES tiles(tile_id),
  rank_score       FLOAT,
  status            TEXT DEFAULT 'pending',            -- pending / confirmed / rejected
  analyst_id         TEXT DEFAULT 'demo_analyst',
  decided_at           TIMESTAMP,
  query_context          JSONB
);

-- ============================================================
-- 6. EXPORTS — provenance-carrying export log
-- ============================================================
CREATE TABLE IF NOT EXISTS exports (
  export_id      SERIAL PRIMARY KEY,
  requested_by     TEXT DEFAULT 'demo_analyst',
  requested_at       TIMESTAMP DEFAULT now(),
  item_ids              INT[],
  format                  TEXT,      -- csv / geojson / pdf
  file_path                 TEXT
);

-- ============================================================
-- 7. SEARCH_LOG — semantic search history
-- ============================================================
CREATE TABLE IF NOT EXISTS search_log (
  search_id       SERIAL PRIMARY KEY,
  analyst_id        TEXT DEFAULT 'demo_analyst',
  raw_query           TEXT,
  query_type            TEXT,      -- 'text' or 'image'
  filters                 JSONB,
  result_tile_ids           TEXT[],
  searched_at                 TIMESTAMP DEFAULT now()
);

-- ============================================================
-- 8. INGESTION_COVERAGE — tracking indexed spatial regions
-- ============================================================
CREATE TABLE IF NOT EXISTS ingestion_coverage (
  region_id       TEXT PRIMARY KEY,
  region_name       TEXT,
  geometry            GEOMETRY(Polygon, 4326),
  status                 TEXT DEFAULT 'pending',    -- pending / in_progress / done
  tile_count                INT DEFAULT 0,
  last_updated                TIMESTAMP DEFAULT now()
);
