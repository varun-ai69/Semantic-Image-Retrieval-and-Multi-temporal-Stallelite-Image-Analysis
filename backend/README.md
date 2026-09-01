# Backend Service (`backend/`)

This directory houses the Python backend services, FastAPI REST API, database models, intent routing agent, ingestion pipelines, model training scripts, and benchmark harnesses.

## Subdirectories:
- `api/`: FastAPI web application endpoints (`search`, `change`, `discovery`, `queue`) and intent routing agent (`intent_router`, tools).
- `db/`: SQLAlchemy models (PostGIS spatial schema), connection setup, and database migrations.
- `services/`: Vector database wrapper (Qdrant client), reranker, quality filtering logic.
- `ingestion/`: Preprocessing scripts, tile embedding, change detection inference, and vector clustering.
- `training/`: Training scripts for fine-tuning RemoteCLIP and change detection models.
- `evaluation/`: Retrieval evaluation, change detection accuracy, and system latency benchmark scripts.
