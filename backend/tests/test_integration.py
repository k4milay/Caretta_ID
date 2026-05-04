"""Integration tests — full HTTP pipeline through FastAPI TestClient.

All heavy dependencies (DB, model weights) are replaced with lightweight
in-memory fakes via FastAPI's dependency_overrides.  This tests routing,
serialisation, error propagation, and agent wiring end-to-end.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from core import dependencies as deps
from repositories.photo_repository import EmbeddingMatch


# ── Shared fakes ──────────────────────────────────────────────────────────────

_TURTLE_ID = uuid.uuid4()
_PHOTO_ID  = uuid.uuid4()

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_turtle():
    return SimpleNamespace(
        id=_TURTLE_ID, name="Athena", notes=None,
        registered_at=_now(), sightings=[],
    )


def _fake_photo():
    return SimpleNamespace(
        id=_PHOTO_ID, turtle_id=_TURTLE_ID,
        file_path="/uploads/x.jpg", uploaded_at=_now(),
    )


def _fake_sighting():
    return SimpleNamespace(
        id=uuid.uuid4(), turtle_id=_TURTLE_ID,
        latitude=36.5, longitude=28.0,
        sighted_at=_now(), location_name="Datça",
    )


def _jpeg() -> bytes:
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def _unit_vec() -> np.ndarray:
    v = np.ones(512, dtype=np.float32)
    return v / np.linalg.norm(v)


# ── Dependency overrides ──────────────────────────────────────────────────────

def _override_turtle_repo():
    t = MagicMock()
    t.create     = AsyncMock(return_value=_fake_turtle())
    t.get_by_id  = AsyncMock(return_value=_fake_turtle())
    t.list_all   = AsyncMock(return_value=[_fake_turtle()])
    t.get_by_ids = AsyncMock(return_value=[_fake_turtle()])
    t.delete     = AsyncMock(return_value=True)
    t._session   = MagicMock()
    t._session.commit  = AsyncMock()
    t._session.refresh = AsyncMock()
    return t


def _override_photo_repo():
    p = MagicMock()
    p.create              = AsyncMock(return_value=_fake_photo())
    p.upsert_embedding    = AsyncMock()
    p.search_by_embedding = AsyncMock(return_value=[
        EmbeddingMatch(_PHOTO_ID, _TURTLE_ID, cosine_distance=0.05)
    ])
    return p


def _override_sighting_repo():
    sr = MagicMock()
    sr.create          = AsyncMock(return_value=_fake_sighting())
    sr.list_for_turtle = AsyncMock(return_value=[_fake_sighting()])
    sr.get_by_id       = AsyncMock(return_value=_fake_sighting())
    return sr


def _prep_agent():
    from agents.base_agent import AgentResult
    from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingOutput
    from services.segmentation.base import SegmentationResult
    roi  = np.zeros((256, 512, 3), dtype=np.uint8)
    mask = np.ones((256, 512), dtype=np.uint8) * 255
    seg  = SegmentationResult(roi=roi, mask=mask, region_name="head")
    out  = PreprocessingOutput(normalised=roi, segmentation=seg, original_size=(512, 512))
    a = MagicMock(spec=ImagePreprocessingAgent)
    a.run = AsyncMock(return_value=AgentResult(ok=True, value=out, error=None, duration_ms=1.0))
    return a


def _feat_agent():
    from agents.base_agent import AgentResult
    from agents.feature_extraction_agent import FeatureExtractionAgent, FeatureOutput
    out = FeatureOutput(embedding=_unit_vec())
    a   = MagicMock(spec=FeatureExtractionAgent)
    a.run = AsyncMock(return_value=AgentResult(ok=True, value=out, error=None, duration_ms=1.0))
    return a


# ── Client fixture ────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    turtle_repo   = _override_turtle_repo()
    photo_repo    = _override_photo_repo()
    sighting_repo = _override_sighting_repo()
    prep          = _prep_agent()
    feat          = _feat_agent()

    # Override leaf repos so CRUD routes work
    app.dependency_overrides[deps.turtle_repo]   = lambda: turtle_repo
    app.dependency_overrides[deps.photo_repo]    = lambda: photo_repo
    app.dependency_overrides[deps.sighting_repo] = lambda: sighting_repo

    # Override composite agents so their internal singleton refs also use fakes
    from agents.orchestrator_agent import OrchestratorAgent
    from agents.similarity_search_agent import SimilaritySearchAgent
    from agents.profile_management_agent import ProfileManagementAgent
    from agents.sighting_tracker_agent import SightingTrackerAgent

    def _orchestrator():
        sim = SimilaritySearchAgent(photo_repo=photo_repo, turtle_repo=turtle_repo)
        return OrchestratorAgent(preprocessing=prep, feature_extraction=feat, similarity_search=sim)

    def _profile():
        return ProfileManagementAgent(
            turtle_repo=turtle_repo, photo_repo=photo_repo,
            preprocessing=prep, feature_extraction=feat,
        )

    def _sighting():
        return SightingTrackerAgent(sighting_repo=sighting_repo, turtle_repo=turtle_repo)

    app.dependency_overrides[deps.orchestrator]    = _orchestrator
    app.dependency_overrides[deps.profile_agent]   = _profile
    app.dependency_overrides[deps.sighting_agent]  = _sighting

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Turtles CRUD ─────────────────────────────────────────────────────────────

def test_create_turtle(client: TestClient):
    r = client.post("/turtles", json={"name": "Athena"})
    assert r.status_code == 201
    assert r.json()["name"] == "Athena"


def test_list_turtles(client: TestClient):
    r = client.get("/turtles")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_turtle(client: TestClient):
    r = client.get(f"/turtles/{_TURTLE_ID}")
    assert r.status_code == 200


def test_delete_turtle(client: TestClient):
    r = client.delete(f"/turtles/{_TURTLE_ID}")
    assert r.status_code == 204


def test_get_nonexistent_turtle_returns_404(client: TestClient):
    app.dependency_overrides[deps.turtle_repo] = lambda: MagicMock(
        get_by_id=AsyncMock(return_value=None)
    )
    r = client.get(f"/turtles/{uuid.uuid4()}")
    assert r.status_code == 404
    app.dependency_overrides[deps.turtle_repo] = lambda: _override_turtle_repo()


# ── Identify ──────────────────────────────────────────────────────────────────

def test_identify_returns_match(client: TestClient):
    r = client.post("/identify", files={"file": ("t.jpg", _jpeg(), "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] is True
    assert len(body["matches"]) == 1
    assert body["matches"][0]["confidence"] == "high"


def test_identify_pipeline_failure_returns_422(client: TestClient):
    """Orchestrator failure surfaces as HTTP 422."""
    from agents.base_agent import AgentResult
    from agents.orchestrator_agent import OrchestratorAgent

    failing_orch = MagicMock(spec=OrchestratorAgent)
    failing_orch.run = AsyncMock(
        return_value=AgentResult(ok=False, value=None, error="bozuk görüntü", duration_ms=1.0)
    )
    app.dependency_overrides[deps.orchestrator] = lambda: failing_orch
    r = client.post("/identify", files={"file": ("t.jpg", _jpeg(), "image/jpeg")})
    assert r.status_code == 422
    assert "bozuk" in r.json()["detail"]
    # Restore
    app.dependency_overrides.pop(deps.orchestrator)


# ── Photos ────────────────────────────────────────────────────────────────────

def test_upload_photo(client: TestClient):
    r = client.post(
        f"/turtles/{_TURTLE_ID}/photos",
        files={"file": ("t.jpg", _jpeg(), "image/jpeg")},
    )
    assert r.status_code == 201
    assert r.json()["turtle_id"] == str(_TURTLE_ID)


# ── Sightings ─────────────────────────────────────────────────────────────────

def test_log_sighting(client: TestClient):
    r = client.post(
        f"/turtles/{_TURTLE_ID}/sightings",
        json={"latitude": 36.5, "longitude": 28.0, "location_name": "Datça"},
    )
    assert r.status_code == 201


def test_list_sightings(client: TestClient):
    r = client.get(f"/turtles/{_TURTLE_ID}/sightings")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_route(client: TestClient):
    # Route requires sighting data; the fake repo returns one sighting
    r = client.get(f"/turtles/{_TURTLE_ID}/route")
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"


# ── Validation errors ─────────────────────────────────────────────────────────

def test_create_turtle_empty_name_rejected(client: TestClient):
    r = client.post("/turtles", json={"name": ""})
    assert r.status_code == 422


def test_log_sighting_out_of_range_lat_rejected(client: TestClient):
    r = client.post(
        f"/turtles/{_TURTLE_ID}/sightings",
        json={"latitude": 999, "longitude": 28.0},
    )
    assert r.status_code == 422
