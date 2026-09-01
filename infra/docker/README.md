# Docker Configurations (`infra/docker`)

Container definitions for service isolation:

- `backend.Dockerfile`: Python environment with GDAL, PyTorch, GeoPandas, and FastAPI.
- `frontend.Dockerfile`: Nginx container serving React application build outputs.
- `titiler.Dockerfile`: FastAPI COG tile server for serving local imagery tiles to Leaflet.
