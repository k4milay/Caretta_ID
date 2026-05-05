"""Expand embedding column from vector(512) to vector(1024).

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-05

Why: New embedding formula concatenates [semantic_512 | spatial_colour_512].
     All existing embeddings must be re-computed (set to NULL here;
     re-upload photos via the UI or POST /api/admin/reembed).
"""
from alembic import op

revision      = "0002"
down_revision = "0001"
branch_labels = None
depends_on    = None

NEW_DIM = 1024
OLD_DIM = 512


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS photos_embedding_hnsw")
    op.execute("ALTER TABLE photos DROP COLUMN IF EXISTS embedding")
    op.execute(f"ALTER TABLE photos ADD COLUMN embedding vector({NEW_DIM})")
    op.execute(
        "CREATE INDEX photos_embedding_hnsw ON photos "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS photos_embedding_hnsw")
    op.execute("ALTER TABLE photos DROP COLUMN IF EXISTS embedding")
    op.execute(f"ALTER TABLE photos ADD COLUMN embedding vector({OLD_DIM})")
    op.execute(
        "CREATE INDEX photos_embedding_hnsw ON photos "
        "USING hnsw (embedding vector_cosine_ops)"
    )
