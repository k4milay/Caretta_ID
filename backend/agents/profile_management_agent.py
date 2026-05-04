"""ProfileManagementAgent — owns the lifecycle of turtle profiles and photos.

Responsibilities (single):
  Create/read/update/delete turtle records and associate photos with them.
  When a photo is added, it is preprocessed and embedded before storage
  so the vector index stays in sync automatically.

Input : ProfileAction  (discriminated union of sub-actions)
Output: ProfileResult  (typed result matching the action)
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from agents.base_agent import BaseAgent
from agents.feature_extraction_agent import FeatureExtractionAgent, FeatureInput
from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput
from models.db import Photo, Turtle
from repositories.photo_repository import PhotoRepository
from repositories.turtle_repository import TurtleRepository

_UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))


# ── Sub-action payloads ────────────────────────────────────────────────────────

@dataclass
class AddPhotoAction:
    kind: Literal["add_photo"] = field(default="add_photo", init=False)
    turtle_id: uuid.UUID
    image_bytes: bytes
    region: str = "head"


@dataclass
class RegisterTurtleAction:
    kind: Literal["register"] = field(default="register", init=False)
    name: str
    notes: str | None = None


@dataclass
class UpdateTurtleAction:
    kind: Literal["update"] = field(default="update", init=False)
    turtle_id: uuid.UUID
    name: str | None = None
    notes: str | None = None


@dataclass
class DeleteTurtleAction:
    kind: Literal["delete"] = field(default="delete", init=False)
    turtle_id: uuid.UUID


ProfileAction = RegisterTurtleAction | UpdateTurtleAction | DeleteTurtleAction | AddPhotoAction


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class ProfileResult:
    turtle: Turtle | None = None
    photo: Photo | None = None
    deleted: bool = False
    message: str = ""


# ── Agent ─────────────────────────────────────────────────────────────────────

class ProfileManagementAgent(BaseAgent[ProfileAction, ProfileResult]):
    name = "ProfileManagement"

    def __init__(
        self,
        turtle_repo: TurtleRepository,
        photo_repo: PhotoRepository,
        preprocessing: ImagePreprocessingAgent,
        feature_extraction: FeatureExtractionAgent,
    ) -> None:
        super().__init__()
        self._turtles = turtle_repo
        self._photos = photo_repo
        self._preprocessing = preprocessing
        self._feature_extraction = feature_extraction

    async def _execute(self, payload: ProfileAction) -> ProfileResult:
        if isinstance(payload, RegisterTurtleAction):
            return await self._register(payload)
        if isinstance(payload, UpdateTurtleAction):
            return await self._update(payload)
        if isinstance(payload, DeleteTurtleAction):
            return await self._delete(payload)
        if isinstance(payload, AddPhotoAction):
            return await self._add_photo(payload)
        raise TypeError(f"Unknown action type: {type(payload)}")

    async def _register(self, action: RegisterTurtleAction) -> ProfileResult:
        turtle = await self._turtles.create(name=action.name, notes=action.notes)
        return ProfileResult(turtle=turtle, message=f"Registered '{turtle.name}' (id={turtle.id})")

    async def _update(self, action: UpdateTurtleAction) -> ProfileResult:
        turtle = await self._turtles.get_by_id(action.turtle_id)
        if not turtle:
            raise ValueError(f"Turtle {action.turtle_id} not found.")
        if action.name:
            turtle.name = action.name
        if action.notes is not None:
            turtle.notes = action.notes
        await self._turtles._session.commit()
        await self._turtles._session.refresh(turtle)
        return ProfileResult(turtle=turtle, message="Profile updated.")

    async def _delete(self, action: DeleteTurtleAction) -> ProfileResult:
        deleted = await self._turtles.delete(action.turtle_id)
        if not deleted:
            raise ValueError(f"Turtle {action.turtle_id} not found.")
        return ProfileResult(deleted=True, message="Turtle and all associated records deleted.")

    async def _add_photo(self, action: AddPhotoAction) -> ProfileResult:
        turtle = await self._turtles.get_by_id(action.turtle_id)
        if not turtle:
            raise ValueError(f"Turtle {action.turtle_id} not found.")

        # Preprocess
        prep_result = await self._preprocessing.run(
            PreprocessingInput(image_bytes=action.image_bytes, region=action.region)
        )
        if not prep_result.ok:
            raise RuntimeError(f"Preprocessing failed: {prep_result.error}")

        # Embed
        feat_result = await self._feature_extraction.run(
            FeatureInput(
                image=prep_result.value.segmentation.roi,
                mask=prep_result.value.segmentation.mask,
            )
        )
        if not feat_result.ok:
            raise RuntimeError(f"Embedding failed: {feat_result.error}")

        # Persist file
        file_path = self._save_file(action.turtle_id, action.image_bytes)

        # Store DB record + embedding
        photo = await self._photos.create(turtle_id=action.turtle_id, file_path=str(file_path))
        await self._photos.upsert_embedding(photo.id, feat_result.value.embedding)

        return ProfileResult(photo=photo, message=f"Photo {photo.id} added and embedded.")

    def _save_file(self, turtle_id: uuid.UUID, data: bytes) -> Path:
        dest_dir = _UPLOAD_DIR / str(turtle_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{uuid.uuid4()}.jpg"
        dest.write_bytes(data)
        return dest
