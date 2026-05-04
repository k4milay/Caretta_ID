"""ImagePreprocessingAgent — validates, normalises, and segments an image.

Input : PreprocessingInput  (raw bytes + optional region hint)
Output: PreprocessingOutput (normalised image array + segmentation result)

Single responsibility: turn a raw uploaded file into a clean, segmented
numpy array ready for feature extraction.  All segmentation logic lives in
the injected SegmentationStrategy, keeping this agent open for extension.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from services.segmentation.base import SegmentationResult, SegmentationStrategy
from services.segmentation.factory import get_strategy

from .base_agent import BaseAgent

# Constants ----------------------------------------------------------------
_MIN_SIDE_PX = 64
_MAX_BYTES = 20 * 1024 * 1024  # 20 MB
_TARGET_SIZE = (512, 512)
_VALID_MAGIC: dict[bytes, str] = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"BM": "bmp",
    b"RIFF": "webp",
}


@dataclass
class PreprocessingInput:
    image_bytes: bytes
    region: str = "head"


@dataclass
class PreprocessingOutput:
    normalised: np.ndarray
    segmentation: SegmentationResult
    original_size: tuple[int, int]


class ImagePreprocessingAgent(BaseAgent[PreprocessingInput, PreprocessingOutput]):
    name = "ImagePreprocessing"

    def __init__(self, strategy: SegmentationStrategy | None = None) -> None:
        super().__init__()
        self._strategy = strategy

    async def _execute(self, payload: PreprocessingInput) -> PreprocessingOutput:
        self._validate_bytes(payload.image_bytes)
        image = self._decode(payload.image_bytes)
        original_size = (image.shape[1], image.shape[0])  # (W, H)
        self._validate_dimensions(image)

        normalised = self._normalise(image)
        strategy = self._strategy or get_strategy(payload.region)
        seg = strategy.segment(normalised)

        return PreprocessingOutput(
            normalised=normalised,
            segmentation=seg,
            original_size=original_size,
        )

    # ------------------------------------------------------------------
    def _validate_bytes(self, data: bytes) -> None:
        if len(data) == 0:
            raise ValueError("Empty image data.")
        if len(data) > _MAX_BYTES:
            raise ValueError(f"Image exceeds {_MAX_BYTES // (1024*1024)} MB limit.")
        header = data[:4]
        if not any(header.startswith(magic) for magic in _VALID_MAGIC):
            raise ValueError("Unsupported image format. Accepted: JPEG, PNG, BMP, WebP.")

    def _decode(self, data: bytes) -> np.ndarray:
        arr = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Image decoding failed — file may be corrupted.")
        return image

    def _validate_dimensions(self, image: np.ndarray) -> None:
        h, w = image.shape[:2]
        if h < _MIN_SIDE_PX or w < _MIN_SIDE_PX:
            raise ValueError(f"Image too small ({w}×{h}). Minimum is {_MIN_SIDE_PX}px per side.")

    def _normalise(self, image: np.ndarray) -> np.ndarray:
        resized = cv2.resize(image, _TARGET_SIZE, interpolation=cv2.INTER_LANCZOS4)
        # CLAHE on L channel of LAB improves contrast consistency across lighting conditions
        lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
