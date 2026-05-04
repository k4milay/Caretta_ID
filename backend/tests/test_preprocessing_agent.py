"""Tests for ImagePreprocessingAgent — no real model, no DB required."""
import io

import cv2
import numpy as np
import pytest

from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput
from services.segmentation.base import SegmentationResult, SegmentationStrategy


def _make_jpeg(width: int = 200, height: int = 200) -> bytes:
    img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


class _IdentityStrategy(SegmentationStrategy):
    region_name = "head"

    def segment(self, image: np.ndarray) -> SegmentationResult:
        mask = np.ones(image.shape[:2], dtype=np.uint8) * 255
        return SegmentationResult(roi=image, mask=mask, region_name=self.region_name)


@pytest.mark.asyncio
async def test_valid_image_produces_output():
    agent = ImagePreprocessingAgent(strategy=_IdentityStrategy())
    result = await agent.run(PreprocessingInput(image_bytes=_make_jpeg()))
    assert result.ok is True
    assert result.value.normalised is not None
    assert result.value.original_size == (200, 200)


@pytest.mark.asyncio
async def test_empty_bytes_fails():
    agent = ImagePreprocessingAgent(strategy=_IdentityStrategy())
    result = await agent.run(PreprocessingInput(image_bytes=b""))
    assert result.ok is False
    assert "Empty" in (result.error or "")


@pytest.mark.asyncio
async def test_invalid_magic_fails():
    agent = ImagePreprocessingAgent(strategy=_IdentityStrategy())
    result = await agent.run(PreprocessingInput(image_bytes=b"NOTANIMAGE" * 100))
    assert result.ok is False
    assert "Unsupported" in (result.error or "")


@pytest.mark.asyncio
async def test_tiny_image_fails():
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    agent = ImagePreprocessingAgent(strategy=_IdentityStrategy())
    result = await agent.run(PreprocessingInput(image_bytes=buf.tobytes()))
    assert result.ok is False
    assert "small" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_normalised_image_is_512x512():
    agent = ImagePreprocessingAgent(strategy=_IdentityStrategy())
    result = await agent.run(PreprocessingInput(image_bytes=_make_jpeg(640, 480)))
    assert result.ok is True
    h, w = result.value.normalised.shape[:2]
    assert (h, w) == (512, 512)
