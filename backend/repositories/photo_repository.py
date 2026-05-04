"""PhotoRepository — all database access for the photos table.

Repository pattern: callers (agents, services) never write raw SQL.
Swapping the backing store (e.g. moving to Qdrant) only requires replacing
this file, not touching any agent code.
"""
from __future__ import annotations

from uuid import UUID

import numpy as np
from pgvector.sqlalchemy import Vector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import Photo


class EmbeddingMatch:
    __slots__ = ("photo_id", "turtle_id", "cosine_distance", "similarity")

    def __init__(self, photo_id: UUID, turtle_id: UUID | None, cosine_distance: float) -> None:
        self.photo_id = photo_id
        self.turtle_id = turtle_id
        self.cosine_distance = cosine_distance
        # cosine distance ∈ [0, 2]; similarity ∈ [0, 1]
        self.similarity = max(0.0, 1.0 - cosine_distance / 2.0)


class PhotoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_embedding(self, photo_id: UUID, embedding: np.ndarray) -> None:
        vec_literal = f"'[{','.join(str(x) for x in embedding.tolist())}]'"
        await self._session.execute(
            text(f"UPDATE photos SET embedding = {vec_literal}::vector WHERE id = :id"),
            {"id": str(photo_id)},
        )
        await self._session.commit()

    async def create(self, turtle_id: UUID | None, file_path: str) -> Photo:
        photo = Photo(turtle_id=turtle_id, file_path=file_path)
        self._session.add(photo)
        await self._session.commit()
        await self._session.refresh(photo)
        return photo

    async def search_by_embedding(
        self,
        embedding: np.ndarray,
        top_k: int = 5,
        exclude_photo_id: UUID | None = None,
    ) -> list[EmbeddingMatch]:
        """Return top-k photos ranked by cosine similarity (HNSW index)."""
        vec_literal = f"'[{','.join(str(x) for x in embedding.tolist())}]'"
        exclude_clause = f"AND id != '{exclude_photo_id}'" if exclude_photo_id else ""
        raw = await self._session.execute(
            text(
                f"SELECT id, turtle_id, embedding <=> {vec_literal}::vector AS dist "
                f"FROM photos WHERE embedding IS NOT NULL {exclude_clause} "
                f"ORDER BY dist LIMIT :k"
            ),
            {"k": top_k},
        )
        return [
            EmbeddingMatch(
                photo_id=UUID(str(row.id)),
                turtle_id=UUID(str(row.turtle_id)) if row.turtle_id else None,
                cosine_distance=float(row.dist),
            )
            for row in raw
        ]

    async def list_by_turtle(self, turtle_id: UUID) -> list[Photo]:
        """Bir kaplumbağaya ait tüm fotoğrafları yükleme tarihine göre döndürür."""
        result = await self._session.execute(
            select(Photo).where(Photo.turtle_id == turtle_id).order_by(Photo.uploaded_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, photo_id: UUID) -> Photo | None:
        result = await self._session.execute(select(Photo).where(Photo.id == photo_id))
        return result.scalar_one_or_none()
