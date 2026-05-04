"""FastAPI dependency providers.

Stateless agents (no per-request state) are module-level singletons.
Repository instances are per-request because they hold an AsyncSession.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agents.feature_extraction_agent import FeatureExtractionAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.preprocessing_agent import ImagePreprocessingAgent
from agents.similarity_search_agent import SimilaritySearchAgent
from core.database import get_session
from repositories.photo_repository import PhotoRepository
from repositories.turtle_repository import TurtleRepository


@lru_cache(maxsize=1)
def preprocessing_agent() -> ImagePreprocessingAgent:
    return ImagePreprocessingAgent()


@lru_cache(maxsize=1)
def feature_extraction_agent() -> FeatureExtractionAgent:
    return FeatureExtractionAgent()


def photo_repo(session: AsyncSession = Depends(get_session)) -> PhotoRepository:
    return PhotoRepository(session)


def turtle_repo(session: AsyncSession = Depends(get_session)) -> TurtleRepository:
    return TurtleRepository(session)


def similarity_search_agent(
    photos: PhotoRepository = Depends(photo_repo),
    turtles: TurtleRepository = Depends(turtle_repo),
) -> SimilaritySearchAgent:
    return SimilaritySearchAgent(photo_repo=photos, turtle_repo=turtles)


def orchestrator(
    similarity: SimilaritySearchAgent = Depends(similarity_search_agent),
) -> OrchestratorAgent:
    return OrchestratorAgent(
        preprocessing=preprocessing_agent(),
        feature_extraction=feature_extraction_agent(),
        similarity_search=similarity,
    )
