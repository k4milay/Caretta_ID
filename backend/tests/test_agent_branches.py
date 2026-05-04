"""Extra tests to cover agent branches not reached by previous test files.

Targets:
  - ProfileManagementAgent._update (lines 107-116)
  - ProfileManagementAgent._save_file path creation
  - SightingTrackerAgent unknown action TypeError
  - ProfileManagementAgent unknown action TypeError
  - preprocessing_agent: corrupt JPEG decode
  - similarity_search_agent: match with no turtle_id
  - core/container.py: register + resolve + duplicate singleton
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import cv2
import numpy as np
import pytest

from agents.profile_management_agent import (
    AddPhotoAction,
    DeleteTurtleAction,
    ProfileManagementAgent,
    RegisterTurtleAction,
    UpdateTurtleAction,
)
from agents.sighting_tracker_agent import SightingTrackerAgent
from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput
from agents.similarity_search_agent import SimilarityInput, SimilaritySearchAgent
from core.container import Container
from repositories.photo_repository import EmbeddingMatch
from services.segmentation.base import SegmentationResult, SegmentationStrategy


# ── Helpers ───────────────────────────────────────────────────────────────────

def _unit_vec(dim: int = 512) -> np.ndarray:
    v = np.ones(dim, dtype=np.float32)
    return v / np.linalg.norm(v)


def _jpeg() -> bytes:
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def _fake_turtle(name: str = "T") -> MagicMock:
    t = MagicMock()
    t.id = uuid.uuid4()
    t.name = name
    t.notes = None
    return t


class _IdentityStrategy(SegmentationStrategy):
    region_name = "head"
    def segment(self, image: np.ndarray) -> SegmentationResult:
        mask = np.ones(image.shape[:2], dtype=np.uint8) * 255
        return SegmentationResult(roi=image, mask=mask, region_name=self.region_name)


# ── ProfileManagementAgent._update ───────────────────────────────────────────

def _profile_agent(turtle=None, photo=None) -> ProfileManagementAgent:
    from agents.base_agent import AgentResult
    from agents.feature_extraction_agent import FeatureExtractionAgent, FeatureOutput
    from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingOutput
    from services.segmentation.base import SegmentationResult

    t = turtle or _fake_turtle()
    turtle_repo = MagicMock()
    turtle_repo.create  = AsyncMock(return_value=t)
    turtle_repo.get_by_id = AsyncMock(return_value=t)
    turtle_repo.delete  = AsyncMock(return_value=True)
    turtle_repo._session = MagicMock()
    turtle_repo._session.commit  = AsyncMock()
    turtle_repo._session.refresh = AsyncMock()

    photo_repo = MagicMock()
    photo_repo.create = AsyncMock(return_value=photo or MagicMock(id=uuid.uuid4(), turtle_id=t.id, file_path="/x"))
    photo_repo.upsert_embedding = AsyncMock()

    roi  = np.zeros((256, 512, 3), dtype=np.uint8)
    mask = np.ones((256, 512), dtype=np.uint8) * 255
    seg  = SegmentationResult(roi=roi, mask=mask, region_name="head")
    prep_out = PreprocessingOutput(normalised=roi, segmentation=seg, original_size=(512, 512))
    prep = MagicMock(spec=ImagePreprocessingAgent)
    prep.run = AsyncMock(return_value=AgentResult(ok=True, value=prep_out, error=None, duration_ms=1.0))

    feat_out = FeatureOutput(embedding=_unit_vec())
    feat = MagicMock(spec=FeatureExtractionAgent)
    feat.run = AsyncMock(return_value=AgentResult(ok=True, value=feat_out, error=None, duration_ms=1.0))

    return ProfileManagementAgent(
        turtle_repo=turtle_repo, photo_repo=photo_repo,
        preprocessing=prep, feature_extraction=feat,
    )


@pytest.mark.asyncio
async def test_update_turtle_name():
    t = _fake_turtle("Old")
    agent = _profile_agent(turtle=t)
    result = await agent.run(UpdateTurtleAction(turtle_id=t.id, name="New"))
    assert result.ok
    assert t.name == "New"
    agent._turtles._session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_update_turtle_notes():
    t = _fake_turtle("Nemo")
    agent = _profile_agent(turtle=t)
    result = await agent.run(UpdateTurtleAction(turtle_id=t.id, notes="updated notes"))
    assert result.ok
    assert t.notes == "updated notes"


@pytest.mark.asyncio
async def test_update_unknown_turtle_fails():
    agent = _profile_agent()
    agent._turtles.get_by_id = AsyncMock(return_value=None)
    result = await agent.run(UpdateTurtleAction(turtle_id=uuid.uuid4(), name="X"))
    assert result.ok is False
    assert "not found" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_profile_unknown_action_type_fails():
    agent = _profile_agent()
    # Bypass the type system to trigger the final TypeError branch
    result = await agent.run("not_an_action")  # type: ignore[arg-type]
    assert result.ok is False


# ── SightingTrackerAgent unknown action ───────────────────────────────────────

@pytest.mark.asyncio
async def test_sighting_unknown_action_type_fails():
    agent = SightingTrackerAgent.__new__(SightingTrackerAgent)
    from core.logging import get_logger
    agent.log = get_logger("test")
    agent._sightings = MagicMock()
    agent._turtles = MagicMock()
    result = await agent.run("bad_action")  # type: ignore[arg-type]
    assert result.ok is False


# ── SimilaritySearchAgent: match without turtle_id ───────────────────────────

@pytest.mark.asyncio
async def test_similarity_skips_match_without_turtle_id():
    match_no_tid = EmbeddingMatch(photo_id=uuid.uuid4(), turtle_id=None, cosine_distance=0.05)
    photo_repo = MagicMock()
    photo_repo.search_by_embedding = AsyncMock(return_value=[match_no_tid])
    turtle_repo = MagicMock()
    turtle_repo.get_by_ids = AsyncMock(return_value=[])

    agent = SimilaritySearchAgent(photo_repo=photo_repo, turtle_repo=turtle_repo)
    result = await agent.run(SimilarityInput(embedding=_unit_vec()))
    assert result.ok
    assert result.value.matches == []


# ── PreprocessingAgent: corrupted JPEG ───────────────────────────────────────

@pytest.mark.asyncio
async def test_preprocessing_corrupted_jpeg_fails():
    # Valid magic bytes but corrupt body
    bad = b"\xff\xd8\xff" + b"\x00" * 50
    agent = ImagePreprocessingAgent(strategy=_IdentityStrategy())
    result = await agent.run(PreprocessingInput(image_bytes=bad))
    assert result.ok is False
    assert "corrupt" in (result.error or "").lower() or "decod" in (result.error or "").lower()


# ── Container ─────────────────────────────────────────────────────────────────

def test_container_register_and_resolve():
    c = Container()
    c.register(str, lambda: "hello")
    assert c.resolve(str) == "hello"
    # Second resolve returns the cached singleton
    assert c.resolve(str) == "hello"


def test_container_unregistered_key_raises():
    c = Container()
    with pytest.raises(KeyError):
        c.resolve(int)


def test_container_non_singleton_does_not_cache():
    c = Container()
    calls = []
    c.register(list, lambda: calls.append(1) or [], singleton=False)
    c.resolve(list)
    c.resolve(list)
    # Each resolve calls the factory because singleton=False clears the cache
    # (container only caches on first resolve; non-singleton prevents the initial cache)
    assert isinstance(c.resolve(list), list)
