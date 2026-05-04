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
from agents.profile_management_agent import ProfileManagementAgent
from agents.sighting_tracker_agent import SightingTrackerAgent
from agents.similarity_search_agent import SimilaritySearchAgent
from core.database import get_session
from repositories.photo_repository import PhotoRepository
from repositories.sighting_repository import SightingRepository
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


def sighting_repo(session: AsyncSession = Depends(get_session)) -> SightingRepository:
    return SightingRepository(session)


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


def profile_agent(
    turtles: TurtleRepository = Depends(turtle_repo),
    photos: PhotoRepository = Depends(photo_repo),
) -> ProfileManagementAgent:
    return ProfileManagementAgent(
        turtle_repo=turtles,
        photo_repo=photos,
        preprocessing=preprocessing_agent(),
        feature_extraction=feature_extraction_agent(),
    )


def sighting_agent(
    sightings: SightingRepository = Depends(sighting_repo),
    turtles: TurtleRepository = Depends(turtle_repo),
) -> SightingTrackerAgent:
    return SightingTrackerAgent(sighting_repo=sightings, turtle_repo=turtles)
