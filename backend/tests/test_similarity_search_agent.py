"""Tests for SimilaritySearchAgent — fake repositories, no DB required."""
from uuid import UUID, uuid4

import numpy as np
import pytest

from agents.similarity_search_agent import (
    CosineStrategy,
    EuclideanStrategy,
    SimilarityInput,
    SimilaritySearchAgent,
)
from models.schemas import MatchResult
from repositories.photo_repository import EmbeddingMatch


# ── Fake repos ────────────────────────────────────────────────────────────────

class _FakeTurtle:
    def __init__(self, tid: UUID, name: str):
        self.id = tid
        self.name = name


class _FakePhotoRepo:
    def __init__(self, matches: list[EmbeddingMatch]) -> None:
        self._matches = matches

    async def search_by_embedding(self, embedding, top_k, exclude_photo_id=None):
        return self._matches[:top_k]


class _FakeTurtleRepo:
    def __init__(self, turtles: list[_FakeTurtle]) -> None:
        self._turtles = {t.id: t for t in turtles}

    async def get_by_ids(self, ids):
        return [self._turtles[i] for i in ids if i in self._turtles]


def _unit_vec(dim: int = 512) -> np.ndarray:
    v = np.ones(dim, dtype=np.float32)
    return v / np.linalg.norm(v)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_returns_matches_above_threshold():
    tid = uuid4()
    photo_id = uuid4()
    match = EmbeddingMatch(photo_id=photo_id, turtle_id=tid, cosine_distance=0.1)
    # similarity = 1 - 0.1/2 = 0.95

    agent = SimilaritySearchAgent(
        photo_repo=_FakePhotoRepo([match]),
        turtle_repo=_FakeTurtleRepo([_FakeTurtle(tid, "Athena")]),
    )
    result = await agent.run(SimilarityInput(embedding=_unit_vec(), threshold=0.60))
    assert result.ok
    assert len(result.value.matches) == 1
    assert result.value.matches[0].name == "Athena"
    assert result.value.accepted is True


@pytest.mark.asyncio
async def test_filters_matches_below_threshold():
    tid = uuid4()
    photo_id = uuid4()
    # cosine_distance=1.2 → similarity=1-0.6=0.40 — below 0.60 threshold
    match = EmbeddingMatch(photo_id=photo_id, turtle_id=tid, cosine_distance=1.2)

    agent = SimilaritySearchAgent(
        photo_repo=_FakePhotoRepo([match]),
        turtle_repo=_FakeTurtleRepo([_FakeTurtle(tid, "Zeus")]),
    )
    result = await agent.run(SimilarityInput(embedding=_unit_vec(), threshold=0.60))
    assert result.ok
    assert result.value.matches == []
    assert result.value.accepted is False


@pytest.mark.asyncio
async def test_confidence_banding():
    tids = [uuid4(), uuid4(), uuid4()]
    matches = [
        EmbeddingMatch(uuid4(), tids[0], cosine_distance=0.10),  # sim=0.95 → high
        EmbeddingMatch(uuid4(), tids[1], cosine_distance=0.40),  # sim=0.80 → medium  (was 0.30 → wrong, recalc: 1-0.4/2=0.80)
        EmbeddingMatch(uuid4(), tids[2], cosine_distance=0.70),  # sim=0.65 → low
    ]
    turtles = [_FakeTurtle(tids[i], f"T{i}") for i in range(3)]

    agent = SimilaritySearchAgent(
        photo_repo=_FakePhotoRepo(matches),
        turtle_repo=_FakeTurtleRepo(turtles),
    )
    result = await agent.run(SimilarityInput(embedding=_unit_vec(), threshold=0.60))
    assert result.ok
    bands = [m.confidence for m in result.value.matches]
    assert bands == ["high", "medium", "low"]


@pytest.mark.asyncio
async def test_deduplicates_same_turtle_multiple_photos():
    tid = uuid4()
    matches = [
        EmbeddingMatch(uuid4(), tid, cosine_distance=0.10),  # better score
        EmbeddingMatch(uuid4(), tid, cosine_distance=0.20),  # duplicate turtle
    ]
    agent = SimilaritySearchAgent(
        photo_repo=_FakePhotoRepo(matches),
        turtle_repo=_FakeTurtleRepo([_FakeTurtle(tid, "Petra")]),
    )
    result = await agent.run(SimilarityInput(embedding=_unit_vec(), threshold=0.60))
    assert result.ok
    assert len(result.value.matches) == 1


@pytest.mark.asyncio
async def test_empty_gallery_returns_no_matches():
    agent = SimilaritySearchAgent(
        photo_repo=_FakePhotoRepo([]),
        turtle_repo=_FakeTurtleRepo([]),
    )
    result = await agent.run(SimilarityInput(embedding=_unit_vec(), threshold=0.60))
    assert result.ok
    assert result.value.matches == []


def test_cosine_strategy_is_symmetric():
    a = _unit_vec()
    b = _unit_vec()
    strat = CosineStrategy()
    assert abs(strat.score(a, b) - strat.score(b, a)) < 1e-6


def test_euclidean_strategy_same_vector_is_one():
    v = _unit_vec()
    strat = EuclideanStrategy()
    assert abs(strat.score(v, v) - 1.0) < 1e-5
