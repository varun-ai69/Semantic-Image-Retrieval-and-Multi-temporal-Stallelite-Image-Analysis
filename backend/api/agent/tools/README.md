# Agent Tools (`backend/api/agent/tools`)

Specific task execution tools invoked by the Intent Router:

- `vector_search.py`: Dispatches semantic queries to Qdrant vector database.
- `spatial_lookup.py`: Queries PostGIS tile registry using spatial intersections (`ST_Intersects`).
- `change_resolver.py`: Evaluates before/after tile pairs and fetches precomputed or live change events.
- `cluster_lookup.py`: Retrieves tiles matching pre-clustered HDBSCAN IDs.
