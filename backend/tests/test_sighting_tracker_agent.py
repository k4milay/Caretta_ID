"""Tests for SightingTrackerAgent — fake repos, no DB."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.sighting_tracker_agent import (
    GetRouteAction,
    ListSightingsAction,
    LogSightingAction,
    SightingTrackerAgent,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_turtle(tid: uuid.UUID | None = None) -> MagicMock:
    t = MagicMock()
    t.id = tid or uuid.uuid4()
    t.name = "Poseidon"
    return t


def _fake_sighting(tid: uuid.UUID, lat: float, lon: float, order: int = 0) -> MagicMock:
    s = MagicMock()
    s.id = uuid.uuid4()
    s.turtle_id = tid
    s.latitude = lat
    s.longitude = lon
    s.location_name = f"Location {order}"
    s.sighted_at = datetime(2024, 1, order + 1, tzinfo=timezone.utc)
    return s


def _make_agent(turtle=None, sightings=None) -> SightingTrackerAgent:
    sighting_repo = MagicMock()
    t = turtle or _fake_turtle()
    sighting_repo.create = AsyncMock(return_value=_fake_sighting(t.id, 36.5, 28.0))
    sighting_repo.list_for_turtle = AsyncMock(return_value=sightings or [])

    turtle_repo = MagicMock()
    turtle_repo.get_by_id = AsyncMock(return_value=t)

    agent = SightingTrackerAgent.__new__(SightingTrackerAgent)
    from core.logging import get_logger
    agent.log = get_logger("test.sighting")
    agent._sightings = sighting_repo
    agent._turtles = turtle_repo
    return agent


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_sighting_returns_sighting():
    tid = uuid.uuid4()
    agent = _make_agent(turtle=_fake_turtle(tid))
    result = await agent.run(
        LogSightingAction(turtle_id=tid, latitude=36.5, longitude=28.0, location_name="Datça")
    )
    assert result.ok
    assert result.value.sighting is not None
    assert result.value.sighting.latitude == 36.5


@pytest.mark.asyncio
async def test_log_sighting_unknown_turtle_fails():
    agent = _make_agent()
    agent._turtles.get_by_id = AsyncMock(return_value=None)
    result = await agent.run(
        LogSightingAction(turtle_id=uuid.uuid4(), latitude=36.0, longitude=28.0)
    )
    assert result.ok is False
    assert "not found" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_get_route_with_two_sightings_produces_linestring():
    tid = uuid.uuid4()
    sightings = [_fake_sighting(tid, 36.0, 28.0, 0), _fake_sighting(tid, 36.5, 28.5, 1)]
    agent = _make_agent(turtle=_fake_turtle(tid), sightings=sightings)
    result = await agent.run(GetRouteAction(turtle_id=tid))
    assert result.ok
    geojson = result.value.geojson
    assert geojson["type"] == "FeatureCollection"
    types = {f["geometry"]["type"] for f in geojson["features"]}
    assert "LineString" in types
    assert "Point" in types


@pytest.mark.asyncio
async def test_get_route_with_one_sighting_has_no_linestring():
    tid = uuid.uuid4()
    agent = _make_agent(turtle=_fake_turtle(tid), sightings=[_fake_sighting(tid, 36.0, 28.0)])
    result = await agent.run(GetRouteAction(turtle_id=tid))
    assert result.ok
    types = {f["geometry"]["type"] for f in result.value.geojson["features"]}
    assert "LineString" not in types


@pytest.mark.asyncio
async def test_list_sightings_returns_ordered_rows():
    tid = uuid.uuid4()
    rows = [_fake_sighting(tid, 36.0 + i * 0.1, 28.0, i) for i in range(3)]
    agent = _make_agent(turtle=_fake_turtle(tid), sightings=rows)
    result = await agent.run(ListSightingsAction(turtle_id=tid))
    assert result.ok
    assert len(result.value.sightings) == 3


@pytest.mark.asyncio
async def test_geojson_coordinates_are_lon_lat_order():
    tid = uuid.uuid4()
    sightings = [_fake_sighting(tid, lat=36.0, lon=28.0, order=0)]
    agent = _make_agent(turtle=_fake_turtle(tid), sightings=sightings)
    result = await agent.run(GetRouteAction(turtle_id=tid))
    point = next(f for f in result.value.geojson["features"] if f["geometry"]["type"] == "Point")
    lon, lat = point["geometry"]["coordinates"]
    assert lon == 28.0  # GeoJSON: longitude first
    assert lat == 36.0
