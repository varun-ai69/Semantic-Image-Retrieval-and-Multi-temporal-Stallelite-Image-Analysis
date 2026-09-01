from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Satellite Imagery Semantic Retrieval & Change Detection API",
    description="Backend service for semantic retrieval and multi-temporal change analysis (PS SIH-26227 for Indian Army DGIS).",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Satellite Imagery Semantic Retrieval & Change Detection API",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=port, reload=True)
