"""Repository unit tests — AsyncMock stands in for SQLAlchemy AsyncSession.

All DB interactions are simulated; no real Postgres connection required.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from repositories.photo_repository import EmbeddingMatch, PhotoRepository
from repositories.sighting_repository import SightingRepository
from repositories.turtle_repository import TurtleRepository


# ── Helpers ───────────────────────────────────────────────────────────────────

def _session() -> MagicMock:
    s = MagicMock()
    s.commit   = AsyncMock()
    s.refresh  = AsyncMock()
    s.execute  = AsyncMock()
    s.add      = MagicMock()
    s.delete   = AsyncMock()
    return s


def _result_mock(value):
    """Simulate session.execute(...) returning a result with scalar_one_or_none."""
    rm = MagicMock()
    rm.scalar_one_or_none.return_value = value
    rm.scalars.return_value.all.return_value = [value] if value else []
    return rm


def _unit_vec(dim: int = 512) -> np.ndarray:
    v = np.ones(dim, dtype=np.float32)
    return v / np.linalg.norm(v)


def _fake_turtle(name: str = "Athena") -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.name = name
    t.notes = None
    t.sightings = []
    return t


def _fake_photo() -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.turtle_id = uuid.uuid4()
    p.file_path = "/uploads/test.jpg"
    return p


def _fake_sighting(tid: uuid.UUID) -> MagicMock:
    s = MagicMock()
    s.id = uuid.uuid4()
    s.turtle_id = tid
    s.latitude = 36.5
    s.longitude = 28.0
    s.sighted_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
    s.location_name = "Datça"
    return s


# ── TurtleRepository ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_turtle_repo_create():
    sess = _session()
    fake = _fake_turtle("Nemo")
    sess.refresh = AsyncMock(side_effect=lambda t: None)

    with patch("repositories.turtle_repository.Turtle", return_value=fake):
        repo = TurtleRepository(sess)
        result = await repo.create("Nemo", notes="test")

    sess.add.assert_called_once_with(fake)
    sess.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_turtle_repo_get_by_id_found():
    sess = _session()
    fake = _fake_turtle("Zeus")
    sess.execute.return_value = _result_mock(fake)

    repo = TurtleRepository(sess)
    result = await repo.get_by_id(fake.id)
    assert result is fake


@pytest.mark.asyncio
async def test_turtle_repo_get_by_id_not_found():
    sess = _session()
    sess.execute.return_value = _result_mock(None)

    repo = TurtleRepository(sess)
    result = await repo.get_by_id(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_turtle_repo_get_by_ids():
    sess = _session()
    fakes = [_fake_turtle(f"T{i}") for i in range(3)]
    rm = MagicMock()
    rm.scalars.return_value.all.return_value = fakes
    sess.execute.return_value = rm

    repo = TurtleRepository(sess)
    results = await repo.get_by_ids([t.id for t in fakes])
    assert len(results) == 3


@pytest.mark.asyncio
async def test_turtle_repo_list_all():
    sess = _session()
    fakes = [_fake_turtle(f"T{i}") for i in range(5)]
    rm = MagicMock()
    rm.scalars.return_value.all.return_value = fakes
    sess.execute.return_value = rm

    repo = TurtleRepository(sess)
    results = await repo.list_all()
    assert len(results) == 5


@pytest.mark.asyncio
async def test_turtle_repo_delete_found():
    sess = _session()
    fake = _fake_turtle()
    sess.execute.return_value = _result_mock(fake)

    repo = TurtleRepository(sess)
    deleted = await repo.delete(fake.id)
    assert deleted is True
    sess.delete.assert_called()


@pytest.mark.asyncio
async def test_turtle_repo_delete_not_found():
    sess = _session()
    sess.execute.return_value = _result_mock(None)

    repo = TurtleRepository(sess)
    deleted = await repo.delete(uuid.uuid4())
    assert deleted is False


# ── PhotoRepository ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_photo_repo_create():
    sess = _session()
    fake = _fake_photo()

    with patch("repositories.photo_repository.Photo", return_value=fake):
        repo = PhotoRepository(sess)
        result = await repo.create(turtle_id=fake.turtle_id, file_path="/uploads/a.jpg")

    sess.add.assert_called_once_with(fake)
    sess.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_photo_repo_get_by_id():
    sess = _session()
    fake = _fake_photo()
    sess.execute.return_value = _result_mock(fake)

    repo = PhotoRepository(sess)
    result = await repo.get_by_id(fake.id)
    assert result is fake


@pytest.mark.asyncio
async def test_photo_repo_upsert_embedding():
    sess = _session()
    repo = PhotoRepository(sess)
    await repo.upsert_embedding(uuid.uuid4(), _unit_vec())
    sess.execute.assert_awaited_once()
    sess.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_photo_repo_search_by_embedding():
    sess = _session()
    tid = uuid.uuid4()
    pid = uuid.uuid4()

    # Simulate raw SQL result rows
    row = MagicMock()
    row.id = pid
    row.turtle_id = tid
    row.dist = 0.1
    rm = MagicMock()
    rm.__iter__ = MagicMock(return_value=iter([row]))
    sess.execute.return_value = rm

    repo = PhotoRepository(sess)
    matches = await repo.search_by_embedding(_unit_vec(), top_k=5)
    assert len(matches) == 1
    assert isinstance(matches[0], EmbeddingMatch)
    assert matches[0].similarity > 0.9


# ── SightingRepository ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sighting_repo_create():
    sess = _session()
    tid = uuid.uuid4()
    fake = _fake_sighting(tid)

    with patch("repositories.sighting_repository.Sighting", return_value=fake):
        repo = SightingRepository(sess)
        result = await repo.create(turtle_id=tid, latitude=36.5, longitude=28.0)

    sess.add.assert_called_once_with(fake)
    sess.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_sighting_repo_list_for_turtle():
    sess = _session()
    tid = uuid.uuid4()
    fakes = [_fake_sighting(tid) for _ in range(4)]
    rm = MagicMock()
    rm.scalars.return_value.all.return_value = fakes
    sess.execute.return_value = rm

    repo = SightingRepository(sess)
    results = await repo.list_for_turtle(tid)
    assert len(results) == 4


@pytest.mark.asyncio
async def test_sighting_repo_get_by_id_found():
    sess = _session()
    tid = uuid.uuid4()
    fake = _fake_sighting(tid)
    sess.execute.return_value = _result_mock(fake)

    repo = SightingRepository(sess)
    result = await repo.get_by_id(fake.id)
    assert result is fake


@pytest.mark.asyncio
async def test_sighting_repo_get_by_id_missing():
    sess = _session()
    sess.execute.return_value = _result_mock(None)

    repo = SightingRepository(sess)
    result = await repo.get_by_id(uuid.uuid4())
    assert result is None
