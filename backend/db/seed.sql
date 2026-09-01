-- seed.sql
-- Final consolidated seed data — one small, coherent demo story so every
-- team member can test their own queries immediately, without waiting on
-- the real ingestion pipeline. Covers every table in schema.sql.
--
-- Story: one site in Ahmedabad, imaged in 2021 and again in 2024, with a
-- construction change detected between them, sitting in the review queue,
-- plus one logged search and one tracked ingestion region.
--
-- To auto-load via docker-compose: mount as
--   /docker-entrypoint-initdb.d/02_seed.sql
-- (runs once, right after schema.sql, same first-start-only rule)

-- ============================================================
-- 1. Scenes
-- ============================================================
INSERT INTO scenes (scene_id, source, acquisition_date, crs, footprint, raw_file_path, provenance)
VALUES
  ('scene_demo_2021', 'sentinel2', '2021-03-10 05:30:00', 'EPSG:4326',
   ST_GeomFromText('POLYGON((72.55 23.00, 72.65 23.00, 72.65 23.10, 72.55 23.10, 72.55 23.00))', 4326),
   '/data/scenes/scene_demo_2021.tif',
   '{"licence": "demo/seed data - not real imagery", "source_note": "placeholder for testing"}'),
  ('scene_demo_2024', 'sentinel2', '2024-03-12 05:30:00', 'EPSG:4326',
   ST_GeomFromText('POLYGON((72.55 23.00, 72.65 23.00, 72.65 23.10, 72.55 23.10, 72.55 23.00))', 4326),
   '/data/scenes/scene_demo_2024.tif',
   '{"licence": "demo/seed data - not real imagery", "source_note": "placeholder for testing"}')
ON CONFLICT (scene_id) DO NOTHING;

-- ============================================================
-- 2. Tiles — same site_key, two dates
-- ============================================================
INSERT INTO tiles (tile_id, scene_id, site_key, geometry, centroid_lat, centroid_lon,
                    acquisition_date, sensor, cloud_pct, registration_residual,
                    quality_confidence, embedding_version, cluster_id,
                    band_count, bit_depth, file_size_bytes, file_path, thumbnail_path)
VALUES
  ('tile_demo_A_2021', 'scene_demo_2021', 'site_23.0225_72.5714',
   ST_GeomFromText('POLYGON((72.5714 23.0225, 72.5814 23.0225, 72.5814 23.0325, 72.5714 23.0325, 72.5714 23.0225))', 4326),
   23.0275, 72.5764, '2021-03-10 05:30:00', 'sentinel2', 0.05, 0.6, 0.93,
   'remoteclip_v1', 'cluster_industrial_01', 4, 16, 1258000,
   '/data/tiles/2021/tile_demo_A_2021.tif', '/data/tiles/2021/thumb_tile_demo_A_2021.jpg'),
  ('tile_demo_A_2024', 'scene_demo_2024', 'site_23.0225_72.5714',
   ST_GeomFromText('POLYGON((72.5714 23.0225, 72.5814 23.0225, 72.5814 23.0325, 72.5714 23.0325, 72.5714 23.0225))', 4326),
   23.0275, 72.5764, '2024-03-12 05:30:00', 'sentinel2', 0.10, 0.8, 0.89,
   'remoteclip_v1', 'cluster_industrial_01', 4, 16, 1301000,
   '/data/tiles/2024/tile_demo_A_2024.tif', '/data/tiles/2024/thumb_tile_demo_A_2024.jpg'),
  -- a second, nearby tile in the same cluster, for testing similarity_discovery
  ('tile_demo_B_2024', 'scene_demo_2024', 'site_23.0300_72.5850',
   ST_GeomFromText('POLYGON((72.5800 23.0250, 72.5900 23.0250, 72.5900 23.0350, 72.5800 23.0350, 72.5800 23.0250))', 4326),
   23.0300, 72.5850, '2024-03-12 05:30:00', 'sentinel2', 0.08, 0.5, 0.91,
   'remoteclip_v1', 'cluster_industrial_01', 4, 16, 1290000,
   '/data/tiles/2024/tile_demo_B_2024.tif', '/data/tiles/2024/thumb_tile_demo_B_2024.jpg'),
  -- a deliberately low-quality tile, for testing the quality gate / 2.2.3
  ('tile_demo_C_2024_cloudy', 'scene_demo_2024', 'site_23.0400_72.5600',
   ST_GeomFromText('POLYGON((72.5550 23.0350, 72.5650 23.0350, 72.5650 23.0450, 72.5550 23.0450, 72.5550 23.0350))', 4326),
   23.0400, 72.5600, '2024-03-12 05:30:00', 'sentinel2', 0.78, 3.2, 0.21,
   'remoteclip_v1', NULL, 4, 16, 1310000,
   '/data/tiles/2024/tile_demo_C_2024_cloudy.tif', '/data/tiles/2024/thumb_tile_demo_C_2024_cloudy.jpg')
ON CONFLICT (tile_id) DO NOTHING;

-- ============================================================
-- 3. Change events
-- ============================================================
INSERT INTO change_events (site_key, tile_before, tile_after, change_type, confidence,
                            earliest_visible_date, model_version, quality_flag)
VALUES
  ('site_23.0225_72.5714', 'tile_demo_A_2021', 'tile_demo_A_2024', 'construction', 0.87,
   '2022-08-15 00:00:00', 'bit_demo_v0', 'ok')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 4. Clusters
-- ============================================================
INSERT INTO clusters (cluster_id, label, model_version)
VALUES
  ('cluster_industrial_01', 'Industrial / warehouse sites (auto-discovered)', 'hdbscan_demo_v0')
ON CONFLICT (cluster_id) DO NOTHING;

-- ============================================================
-- 5. Review queue — one pending item referencing the change event above
-- ============================================================
INSERT INTO review_items (event_id, tile_id, rank_score, status, query_context)
SELECT event_id, 'tile_demo_A_2024', 0.87, 'pending',
       '{"source": "change_query", "aoi_note": "seed demo item"}'
FROM change_events WHERE site_key = 'site_23.0225_72.5714'
LIMIT 1;

-- ============================================================
-- 6. Search log — one example logged search
-- ============================================================
INSERT INTO search_log (raw_query, query_type, filters, result_tile_ids)
VALUES
  ('newly built structures near a river', 'text',
   '{"aoi": null, "date_range": null, "sensor": null}',
   ARRAY['tile_demo_A_2024', 'tile_demo_B_2024']);

-- ============================================================
-- 7. Ingestion coverage
-- ============================================================
INSERT INTO ingestion_coverage (region_id, region_name, geometry, status, tile_count)
VALUES
  ('region_ahd_demo', 'Ahmedabad (demo seed region)',
   ST_GeomFromText('POLYGON((72.55 23.00, 72.65 23.00, 72.65 23.10, 72.55 23.10, 72.55 23.00))', 4326),
   'in_progress', 4)
ON CONFLICT (region_id) DO NOTHING;