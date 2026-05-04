"""SQLAlchemy ORM models. Single source of truth for the relational schema."""
from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.config import get_settings
from core.database import Base

EMBEDDING_DIM = get_settings().embedding_dim


class Turtle(Base):
    __tablename__ = "turtles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    photos: Mapped[list["Photo"]] = relationship(back_populates="turtle", cascade="all, delete-orphan")
    sightings: Mapped[list["Sighting"]] = relationship(back_populates="turtle", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    turtle_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("turtles.id", ondelete="CASCADE"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(String(500))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    turtle: Mapped["Turtle | None"] = relationship(back_populates="photos")


class Sighting(Base):
    __tablename__ = "sightings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    turtle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("turtles.id", ondelete="CASCADE")
    )
    photo_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("photos.id", ondelete="SET NULL"), nullable=True
    )
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    sighted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    location_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    turtle: Mapped["Turtle"] = relationship(back_populates="sightings")
