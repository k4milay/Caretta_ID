"""SightingTrackerAgent — records GPS sightings and generates GeoJSON routes.

Responsibilities (single):
  Log a new sighting for a known turtle, update its location history,
  and produce a GeoJSON LineString representing the full movement route.

Input : SightingAction  (log a sighting OR request the route)
Output: SightingResult  (logged Sighting OR GeoJSON FeatureCollection)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from agents.base_agent import BaseAgent
from models.db import Sighting
from repositories.sighting_repository import SightingRepository
from repositories.turtle_repository import TurtleRepository


# ── Sub-action payloads ────────────────────────────────────────────────────────

@dataclass
class LogSightingAction:
    kind: Literal["log"] = field(default="log", init=False)
    turtle_id: uuid.UUID
    latitude: float
    longitude: float
    location_name: str | None = None
    photo_id: uuid.UUID | None = None


@dataclass
class GetRouteAction:
    kind: Literal["route"] = field(default="route", init=False)
    turtle_id: uuid.UUID


@dataclass
class ListSightingsAction:
    kind: Literal["list"] = field(default="list", init=False)
    turtle_id: uuid.UUID


SightingAction = LogSightingAction | GetRouteAction | ListSightingsAction


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class SightingResult:
    sighting: Sighting | None = None
    sightings: list[Sighting] = field(default_factory=list)
    geojson: dict[str, Any] | None = None


# ── Agent ─────────────────────────────────────────────────────────────────────

class SightingTrackerAgent(BaseAgent[SightingAction, SightingResult]):
    name = "SightingTracker"

    def __init__(
        self,
        sighting_repo: SightingRepository,
        turtle_repo: TurtleRepository,
    ) -> None:
        super().__init__()
        self._sightings = sighting_repo
        self._turtles = turtle_repo

    async def _execute(self, payload: SightingAction) -> SightingResult:
        if isinstance(payload, LogSightingAction):
            return await self._log(payload)
        if isinstance(payload, GetRouteAction):
            return await self._route(payload)
        if isinstance(payload, ListSightingsAction):
            return await self._list(payload)
        raise TypeError(f"Unknown action: {type(payload)}")

    async def _log(self, action: LogSightingAction) -> SightingResult:
        turtle = await self._turtles.get_by_id(action.turtle_id)
        if not turtle:
            raise ValueError(f"Turtle {action.turtle_id} not found.")
        sighting = await self._sightings.create(
            turtle_id=action.turtle_id,
            latitude=action.latitude,
            longitude=action.longitude,
            location_name=action.location_name,
            photo_id=action.photo_id,
        )
        return SightingResult(sighting=sighting)

    async def _route(self, action: GetRouteAction) -> SightingResult:
        turtle = await self._turtles.get_by_id(action.turtle_id)
        if not turtle:
            raise ValueError(f"Turtle {action.turtle_id} not found.")
        sightings = await self._sightings.list_for_turtle(action.turtle_id)
        geojson = self._build_geojson(turtle.name, sightings)
        return SightingResult(geojson=geojson)

    async def _list(self, action: ListSightingsAction) -> SightingResult:
        turtle = await self._turtles.get_by_id(action.turtle_id)
        if not turtle:
            raise ValueError(f"Turtle {action.turtle_id} not found.")
        rows = await self._sightings.list_for_turtle(action.turtle_id)
        return SightingResult(sightings=rows)

    @staticmethod
    def _build_geojson(turtle_name: str, sightings: list[Sighting]) -> dict[str, Any]:
        """GeoJSON FeatureCollection: one Point per sighting + one LineString route."""
        points = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [s.longitude, s.latitude],
                },
                "properties": {
                    "id": str(s.id),
                    "sighted_at": s.sighted_at.isoformat(),
                    "location_name": s.location_name,
                    "order": i,
                },
            }
            for i, s in enumerate(sightings)
        ]

        features: list[dict] = points
        if len(sightings) >= 2:
            coords = [[s.longitude, s.latitude] for s in sightings]
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {"turtle_name": turtle_name, "sighting_count": len(sightings)},
                }
            )

        return {
            "type": "FeatureCollection",
            "properties": {"turtle_name": turtle_name},
            "features": features,
        }
