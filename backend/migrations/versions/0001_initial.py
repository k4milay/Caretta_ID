"""initial schema with pgvector

Revision ID: 0001
Revises:
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 512


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "turtles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "photos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("turtle_id", UUID(as_uuid=True), sa.ForeignKey("turtles.id", ondelete="CASCADE"), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # HNSW index for cosine similarity search on embeddings
    op.execute(
        "CREATE INDEX photos_embedding_hnsw ON photos "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "sightings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("turtle_id", UUID(as_uuid=True), sa.ForeignKey("turtles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("photo_id", UUID(as_uuid=True), sa.ForeignKey("photos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("sighted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("location_name", sa.String(200), nullable=True),
    )
    op.create_index("ix_sightings_turtle_id", "sightings", ["turtle_id"])
    op.create_index("ix_sightings_sighted_at", "sightings", ["sighted_at"])


def downgrade() -> None:
    op.drop_index("ix_sightings_sighted_at", "sightings")
    op.drop_index("ix_sightings_turtle_id", "sightings")
    op.drop_table("sightings")
    op.execute("DROP INDEX IF EXISTS photos_embedding_hnsw")
    op.drop_table("photos")
    op.drop_table("turtles")
