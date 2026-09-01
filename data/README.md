# Data Storage (`data/`)

This directory is used for local data staging and image storage. All raw imagery, tiles, and training datasets stored here are git-ignored.

- `raw/`: Unprocessed satellite scenes and Cloud-Optimized GeoTIFFs (COGs).
- `tiles/`: Preprocessed 512x512 tile patches formatted for ingestion into PostGIS and Qdrant.
- `training/`: Staged datasets for model fine-tuning (e.g. RSICD, RSITMD, LEVIR-CD, OSCD).
