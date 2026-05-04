"""Sighting routes — log GPS sightings and retrieve movement routes."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from agents.sighting_tracker_agent import (
    GetRouteAction,
    ListSightingsAction,
    LogSightingAction,
    SightingTrackerAgent,
)
from core.dependencies import sighting_agent
from models.schemas import SightingBody, SightingRead

router = APIRouter(prefix="/turtles/{turtle_id}", tags=["sightings"])


@router.post("/sightings", response_model=SightingRead, status_code=status.HTTP_201_CREATED)
async def log_sighting(
    turtle_id: UUID,
    body: SightingBody,
    agent: SightingTrackerAgent = Depends(sighting_agent),
) -> SightingRead:
    """Record a GPS sighting for a turtle."""
    result = await agent.run(
        LogSightingAction(
            turtle_id=turtle_id,
            latitude=body.latitude,
            longitude=body.longitude,
            location_name=body.location_name,
            photo_id=body.photo_id,
        )
    )
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.error)
    return SightingRead.model_validate(result.value.sighting)


@router.get("/sightings", response_model=list[SightingRead])
async def list_sightings(
    turtle_id: UUID,
    agent: SightingTrackerAgent = Depends(sighting_agent),
) -> list[SightingRead]:
    """Return all sightings for a turtle in chronological order."""
    result = await agent.run(ListSightingsAction(turtle_id=turtle_id))
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.error)
    return [SightingRead.model_validate(s) for s in result.value.sightings]


@router.get("/route")
async def get_route(
    turtle_id: UUID,
    agent: SightingTrackerAgent = Depends(sighting_agent),
) -> dict[str, Any]:
    """Return a GeoJSON FeatureCollection of all sightings + route LineString."""
    result = await agent.run(GetRouteAction(turtle_id=turtle_id))
    if not result.ok:
        raise HTTPException(status_code=422, detail=result.error)
    return result.value.geojson
