# Frontend Application (`frontend/`)

This directory contains the React + Leaflet web application for satellite imagery search, multi-temporal change review, and analyst decision management.

## Subdirectories:
- `src/components/`: Reusable UI components including map view (`MapView`), AOI drawing (`AOIDrawTool`), pinpoint mode (`PinPointTool`), search bar (`SearchBar`), results grid (`ResultsGrid`), change detail slider (`LocationDetail`), review queue (`ReviewQueue`), and cluster map (`ClusterMapView`).
- `src/pages/`: Page views for the main dashboard, search, change detection analysis, and analyst queues.
- `src/api/`: REST API client layer connecting the frontend UI to backend endpoints.
