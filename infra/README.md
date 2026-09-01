# Infrastructure & Packaging (`infra/`)

This directory contains container configurations and utility scripts for managing the system in an offline, on-premises environment.

## Subdirectories:
- `docker/`: Dockerfiles for containerizing the backend (`backend.Dockerfile`), frontend (`frontend.Dockerfile`), and tile server (`titiler.Dockerfile`).
- `scripts/`: Shell scripts for pre-staging offline dependencies (`stage_offline_deps.sh`) and verifying offline operation (`test_offline_mode.sh`).
