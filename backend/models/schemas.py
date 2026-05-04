"""Pydantic schemas for API I/O."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TurtleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    notes: str | None = None


class TurtleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    notes: str | None
    registered_at: datetime


class SightingCreate(BaseModel):
    turtle_id: UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str | None = None
    photo_id: UUID | None = None


class SightingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    turtle_id: UUID
    latitude: float
    longitude: float
    sighted_at: datetime
    location_name: str | None


class TurtleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    notes: str | None = None


class PhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    turtle_id: UUID | None
    file_path: str
    uploaded_at: datetime


class SightingBody(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str | None = None
    photo_id: UUID | None = None


class MatchResult(BaseModel):
    turtle_id: UUID
    name: str
    similarity_score: float
    confidence: str


class IdentificationResponse(BaseModel):
    matches: list[MatchResult]
    threshold: float
    accepted: bool
