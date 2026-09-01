# Ingestion Pipelines (`backend/ingestion`)

Scripts for ingestion-time processing of new satellite scenes.

- `preprocess.py`: CRS reprojection, 512x512 tiling, cloud masking (`s2cloudless`), histogram matching, and sub-pixel co-registration (`AROSICS`).
- `embed_and_store.py`: Inference pass through RemoteCLIP encoder and vector upsert into Qdrant.
- `change_detect.py`: Precalculates change events between co-registered before/after tiles and logs to PostGIS.
- `cluster.py`: Runs HDBSCAN over Qdrant embeddings to assign discovery cluster IDs.
