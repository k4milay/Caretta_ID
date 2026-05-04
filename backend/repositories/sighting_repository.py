"""SightingRepository — all database access for the sightings table."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import Sighting


class SightingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        turtle_id: uuid.UUID,
        latitude: float,
        longitude: float,
        location_name: str | None = None,
        photo_id: uuid.UUID | None = None,
    ) -> Sighting:
        sighting = Sighting(
            turtle_id=turtle_id,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            photo_id=photo_id,
        )
        self._session.add(sighting)
        await self._session.commit()
        await self._session.refresh(sighting)
        return sighting

    async def list_for_turtle(self, turtle_id: uuid.UUID) -> list[Sighting]:
        result = await self._session.execute(
            select(Sighting)
            .where(Sighting.turtle_id == turtle_id)
            .order_by(Sighting.sighted_at)
        )
        return list(result.scalars().all())

    async def get_by_id(self, sighting_id: uuid.UUID) -> Sighting | None:
        result = await self._session.execute(
            select(Sighting).where(Sighting.id == sighting_id)
        )
        return result.scalar_one_or_none()
