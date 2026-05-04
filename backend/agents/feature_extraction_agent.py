"""FeatureExtractionAgent — converts a preprocessed image into a 512-d embedding.

Input : FeatureInput  (normalised image array from PreprocessingAgent)
Output: FeatureOutput (embedding vector, dim, model version)

The embedding function is injected at construction so tests can supply a
deterministic fake without loading PyTorch weights.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from services.embedding_model import EMBEDDING_DIM, embed_image

from .base_agent import BaseAgent

EmbedFn = Callable[[np.ndarray], np.ndarray]


@dataclass
class FeatureInput:
    image: np.ndarray
    mask: np.ndarray | None = None  # optional binary spot mask to focus embedding


@dataclass
class FeatureOutput:
    embedding: np.ndarray
    dim: int = field(init=False)
    model_version: str = "efficientnet-b0-v1"

    def __post_init__(self) -> None:
        self.dim = len(self.embedding)


class FeatureExtractionAgent(BaseAgent[FeatureInput, FeatureOutput]):
    name = "FeatureExtraction"

    def __init__(self, embed_fn: EmbedFn = embed_image) -> None:
        super().__init__()
        self._embed = embed_fn

    async def _execute(self, payload: FeatureInput) -> FeatureOutput:
        image = self._apply_mask(payload.image, payload.mask)
        embedding = self._embed(image)
        self._validate_embedding(embedding)
        return FeatureOutput(embedding=embedding)

    # ------------------------------------------------------------------
    def _apply_mask(self, image: np.ndarray, mask: np.ndarray | None) -> np.ndarray:
        if mask is None or not mask.any():
            return image
        # Zero out background pixels — focuses the model on spot regions
        masked = image.copy()
        masked[mask == 0] = 0
        return masked

    def _validate_embedding(self, vec: np.ndarray) -> None:
        if vec.ndim != 1 or len(vec) < 128:
            raise ValueError(f"Invalid embedding shape: {vec.shape}. Expected 1-D with ≥128 dims.")
        norm = float(np.linalg.norm(vec))
        if not (0.9 <= norm <= 1.1):
            raise ValueError(f"Embedding is not unit-normalised (norm={norm:.4f}).")
