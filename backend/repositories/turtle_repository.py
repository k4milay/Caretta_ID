"""TurtleRepository — CRUD access for the turtles table."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.db import Turtle


class TurtleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, notes: str | None = None) -> Turtle:
        turtle = Turtle(name=name, notes=notes)
        self._session.add(turtle)
        await self._session.commit()
        await self._session.refresh(turtle)
        return turtle

    async def get_by_id(self, turtle_id: UUID) -> Turtle | None:
        result = await self._session.execute(
            select(Turtle).where(Turtle.id == turtle_id).options(selectinload(Turtle.sightings))
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[UUID]) -> list[Turtle]:
        result = await self._session.execute(select(Turtle).where(Turtle.id.in_(ids)))
        return list(result.scalars().all())

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Turtle]:
        result = await self._session.execute(select(Turtle).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def delete(self, turtle_id: UUID) -> bool:
        turtle = await self.get_by_id(turtle_id)
        if not turtle:
            return False
        await self._session.delete(turtle)
        await self._session.commit()
        return True
