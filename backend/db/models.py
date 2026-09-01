"""
SQLAlchemy and Pydantic models for PostgreSQL / PostGIS schema validation.
Matches schema.sql perfectly.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    ARRAY,
    func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
from pydantic import BaseModel, Field

Base = declarative_base()

# ============================================================
# 1. SQLAlchemy ORM Models (matching schema.sql)
# ============================================================

class Scene(Base):
    __tablename__ = "scenes"

    scene_id = Column(String, primary_key=True)
    source = Column(String, nullable=True)
    acquisition_date = Column(DateTime, nullable=True)
    crs = Column(String, nullable=True)
    footprint = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    ingested_at = Column(DateTime, server_default=func.now())
    raw_file_path = Column(String, nullable=True)
    provenance = Column(JSONB, nullable=True)

    tiles = relationship("Tile", back_populates="scene")


class Tile(Base):
    __tablename__ = "tiles"

    tile_id = Column(String, primary_key=True)
    scene_id = Column(String, ForeignKey("scenes.scene_id"), nullable=True)
    site_key = Column(String, nullable=True, index=True)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)
    acquisition_date = Column(DateTime, nullable=True, index=True)
    sensor = Column(String, nullable=True)
    cloud_pct = Column(Float, nullable=True)
    quality_confidence = Column(Float, nullable=True)
    cluster_id = Column(String, nullable=True, index=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    scene = relationship("Scene", back_populates="tiles")


class ChangeEvent(Base):
    __tablename__ = "change_events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    site_key = Column(String, nullable=True, index=True)
    tile_before = Column(String, ForeignKey("tiles.tile_id"), nullable=False)
    tile_after = Column(String, ForeignKey("tiles.tile_id"), nullable=False)
    change_type = Column(String, nullable=True)
    confidence = Column(Float, nullable=False, index=True)
    earliest_visible_date = Column(DateTime, nullable=True)
    detected_date = Column(DateTime, server_default=func.now(), index=True)
    model_version = Column(String, nullable=True)
    quality_flag = Column(String, default="ok")


class Cluster(Base):
    __tablename__ = "clusters"

    cluster_id = Column(String, primary_key=True)
    label = Column(String, nullable=True)
    computed_at = Column(DateTime, server_default=func.now())
    model_version = Column(String, nullable=True)


class ReviewItem(Base):
    __tablename__ = "review_items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("change_events.event_id"), nullable=True)
    tile_id = Column(String, ForeignKey("tiles.tile_id"), nullable=True)
    rank_score = Column(Float, nullable=True)
    status = Column(String, default="pending")
    analyst_id = Column(String, default="demo_analyst")
    decided_at = Column(DateTime, nullable=True)
    query_context = Column(JSONB, nullable=True)


class Export(Base):
    __tablename__ = "exports"

    export_id = Column(Integer, primary_key=True, autoincrement=True)
    requested_by = Column(String, default="demo_analyst")
    requested_at = Column(DateTime, server_default=func.now())
    item_ids = Column(ARRAY(Integer), nullable=False)
    format = Column(String, nullable=False)
    file_path = Column(String, nullable=True)


class SearchLog(Base):
    __tablename__ = "search_log"

    search_id = Column(Integer, primary_key=True, autoincrement=True)
    analyst_id = Column(String, default="demo_analyst")
    raw_query = Column(String, nullable=False)
    query_type = Column(String, default="text")
    filters = Column(JSONB, nullable=True)
    result_tile_ids = Column(ARRAY(String), nullable=True)
    searched_at = Column(DateTime, server_default=func.now())


class IngestionCoverage(Base):
    __tablename__ = "ingestion_coverage"

    region_id = Column(String, primary_key=True)
    region_name = Column(String, nullable=True)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    status = Column(String, default="pending")
    tile_count = Column(Integer, default=0)
    last_updated = Column(DateTime, server_default=func.now())


# ============================================================
# 2. Pydantic Schemas for API / Schema Validation
# ============================================================

class SceneSchema(BaseModel):
    scene_id: str
    source: Optional[str] = None
    acquisition_date: Optional[datetime] = None
    crs: Optional[str] = None
    raw_file_path: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TileSchema(BaseModel):
    tile_id: str
    scene_id: Optional[str] = None
    site_key: Optional[str] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    acquisition_date: Optional[datetime] = None
    sensor: Optional[str] = None
    cloud_pct: Optional[float] = None
    quality_confidence: Optional[float] = None
    cluster_id: Optional[str] = None
    file_path: Optional[str] = None

    class Config:
        from_attributes = True


class ChangeEventSchema(BaseModel):
    event_id: Optional[int] = None
    site_key: Optional[str] = None
    tile_before: str
    tile_after: str
    change_type: Optional[str] = None
    confidence: float
    earliest_visible_date: Optional[datetime] = None
    detected_date: Optional[datetime] = None
    model_version: Optional[str] = None
    quality_flag: Optional[str] = "ok"

    class Config:
        from_attributes = True


class ClusterSchema(BaseModel):
    cluster_id: str
    label: Optional[str] = None
    computed_at: Optional[datetime] = None
    model_version: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewItemSchema(BaseModel):
    item_id: Optional[int] = None
    event_id: Optional[int] = None
    tile_id: Optional[str] = None
    rank_score: Optional[float] = None
    status: str = "pending"
    analyst_id: str = "demo_analyst"
    decided_at: Optional[datetime] = None
    query_context: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
