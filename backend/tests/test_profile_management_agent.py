"""Tests for ProfileManagementAgent — all dependencies faked, no DB/GPU."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import cv2
import numpy as np
import pytest

from agents.base_agent import AgentResult
from agents.feature_extraction_agent import FeatureExtractionAgent, FeatureOutput
from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingOutput
from agents.profile_management_agent import (
    AddPhotoAction,
    DeleteTurtleAction,
    ProfileManagementAgent,
    RegisterTurtleAction,
    UpdateTurtleAction,
)
from services.segmentation.base import SegmentationResult


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_jpeg() -> bytes:
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def _unit_vec(dim: int = 512) -> np.ndarray:
    v = np.ones(dim, dtype=np.float32)
    return v / np.linalg.norm(v)


def _fake_turtle(name: str = "Athena") -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.name = name
    t.notes = None
    return t


def _fake_photo() -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.turtle_id = uuid.uuid4()
    p.file_path = "/uploads/test.jpg"
    return p


def _make_prep_agent(ok: bool = True) -> ImagePreprocessingAgent:
    agent = MagicMock(spec=ImagePreprocessingAgent)
    if ok:
        roi = np.zeros((256, 512, 3), dtype=np.uint8)
        mask = np.ones((256, 512), dtype=np.uint8) * 255
        seg = SegmentationResult(roi=roi, mask=mask, region_name="head")
        output = PreprocessingOutput(
            normalised=roi, segmentation=seg, original_size=(512, 512)
        )
        agent.run = AsyncMock(return_value=AgentResult(ok=True, value=output, error=None, duration_ms=1.0))
    else:
        agent.run = AsyncMock(return_value=AgentResult(ok=False, value=None, error="bad image", duration_ms=1.0))
    return agent


def _make_feat_agent(ok: bool = True) -> FeatureExtractionAgent:
    agent = MagicMock(spec=FeatureExtractionAgent)
    if ok:
        output = FeatureOutput(embedding=_unit_vec())
        agent.run = AsyncMock(return_value=AgentResult(ok=True, value=output, error=None, duration_ms=1.0))
    else:
        agent.run = AsyncMock(return_value=AgentResult(ok=False, value=None, error="embed fail", duration_ms=1.0))
    return agent


def _make_agent(turtle=None, photo=None, prep_ok=True, feat_ok=True) -> ProfileManagementAgent:
    turtle_repo = MagicMock()
    turtle_repo.create = AsyncMock(return_value=turtle or _fake_turtle())
    turtle_repo.get_by_id = AsyncMock(return_value=turtle or _fake_turtle())
    turtle_repo.delete = AsyncMock(return_value=True)
    turtle_repo._session = MagicMock()
    turtle_repo._session.commit = AsyncMock()
    turtle_repo._session.refresh = AsyncMock()

    photo_repo = MagicMock()
    photo_repo.create = AsyncMock(return_value=photo or _fake_photo())
    photo_repo.upsert_embedding = AsyncMock()

    return ProfileManagementAgent(
        turtle_repo=turtle_repo,
        photo_repo=photo_repo,
        preprocessing=_make_prep_agent(ok=prep_ok),
        feature_extraction=_make_feat_agent(ok=feat_ok),
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_turtle():
    fake = _fake_turtle("Nemo")
    agent = _make_agent(turtle=fake)
    result = await agent.run(RegisterTurtleAction(name="Nemo", notes="test turtle"))
    assert result.ok
    assert result.value.turtle.name == "Nemo"


@pytest.mark.asyncio
async def test_delete_turtle():
    agent = _make_agent()
    result = await agent.run(DeleteTurtleAction(turtle_id=uuid.uuid4()))
    assert result.ok
    assert result.value.deleted is True


@pytest.mark.asyncio
async def test_delete_missing_turtle_fails():
    agent = _make_agent()
    agent._turtles.get_by_id = AsyncMock(return_value=None)
    agent._turtles.delete = AsyncMock(return_value=False)
    result = await agent.run(DeleteTurtleAction(turtle_id=uuid.uuid4()))
    assert result.ok is False
    assert "not found" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_add_photo_stores_embedding(tmp_path, monkeypatch):
    import agents.profile_management_agent as mod
    monkeypatch.setattr(mod, "_UPLOAD_DIR", tmp_path)

    fake_photo = _fake_photo()
    agent = _make_agent(photo=fake_photo)
    result = await agent.run(
        AddPhotoAction(turtle_id=uuid.uuid4(), image_bytes=_make_jpeg())
    )
    assert result.ok
    assert result.value.photo.id == fake_photo.id
    agent._photos.upsert_embedding.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_photo_preprocessing_failure_propagates():
    agent = _make_agent(prep_ok=False)
    result = await agent.run(
        AddPhotoAction(turtle_id=uuid.uuid4(), image_bytes=_make_jpeg())
    )
    assert result.ok is False
    assert "Preprocessing" in (result.error or "")


@pytest.mark.asyncio
async def test_add_photo_for_unknown_turtle_fails():
    agent = _make_agent()
    agent._turtles.get_by_id = AsyncMock(return_value=None)
    result = await agent.run(
        AddPhotoAction(turtle_id=uuid.uuid4(), image_bytes=_make_jpeg())
    )
    assert result.ok is False
    assert "not found" in (result.error or "").lower()
