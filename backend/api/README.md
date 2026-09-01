# FastAPI API Application (`backend/api`)

This folder contains the FastAPI application entrypoint, endpoint routers, and the intent routing agent.

All API routes follow the `/api/v1` version prefix format:

## Base API Path: `/api/v1`

### Endpoints Overview:
- `POST /api/v1/search`: Text & Image semantic search endpoints.
- `POST /api/v1/change`: AOI polygon & date-range change resolution endpoints.
- `GET /api/v1/discover/{tile_id}`: Cluster discovery & similar tile endpoints.
- `GET/POST /api/v1/queue`: Analyst review queue & decision log endpoints.
- `POST /api/v1/export`: Report generation & export endpoints (GeoJSON/CSV/PDF).

## Subdirectories:
- `main.py`: FastAPI server entrypoint mounting `/api/v1` router prefix.
- `routers/`: Endpoint modules (`search.py`, `change.py`, `discovery.py`, `queue.py`).
- `agent/`: Intent routing agent (`intent_router.py`) and specialized tools (`vector_search`, `spatial_lookup`, `change_resolver`, `cluster_lookup`).
