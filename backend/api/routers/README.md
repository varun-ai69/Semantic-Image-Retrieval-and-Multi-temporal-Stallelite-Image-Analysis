# API Routers (`backend/api/routers`)

This folder contains FastAPI REST route handlers mounted under the `/api/v1` prefix:

- `search.py` -> `POST /api/v1/search`: Handles semantic text-to-image and image-to-image similarity search endpoints.
- `change.py` -> `POST /api/v1/change`: Handles AOI polygon and date-range change resolution endpoints.
- `discovery.py` -> `GET /api/v1/discover/{tile_id}`: Handles tile clustering and similarity discovery endpoints.
- `queue.py` -> `GET/POST /api/v1/queue`: Handles analyst review queue item retrieval and confirmation/rejection logging.
- `export.py` -> `POST /api/v1/export`: Handles intelligence evidence report exporting.
