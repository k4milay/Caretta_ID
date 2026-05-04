"""Tests for FeatureExtractionAgent — uses a fake embed_fn, no PyTorch needed."""
import numpy as np
import pytest

from agents.feature_extraction_agent import FeatureExtractionAgent, FeatureInput


def _fake_embed(image: np.ndarray) -> np.ndarray:
    vec = np.ones(512, dtype=np.float32)
    return vec / np.linalg.norm(vec)


def _random_image(h: int = 512, w: int = 512) -> np.ndarray:
    return np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)


@pytest.mark.asyncio
async def test_returns_512d_unit_vector():
    agent = FeatureExtractionAgent(embed_fn=_fake_embed)
    result = await agent.run(FeatureInput(image=_random_image()))
    assert result.ok is True
    assert result.value.dim == 512
    norm = float(np.linalg.norm(result.value.embedding))
    assert abs(norm - 1.0) < 1e-5


@pytest.mark.asyncio
async def test_mask_zeroes_background():
    calls: list[np.ndarray] = []

    def _capturing_embed(img: np.ndarray) -> np.ndarray:
        calls.append(img.copy())
        vec = np.random.rand(512).astype(np.float32)
        return vec / np.linalg.norm(vec)

    image = np.ones((512, 512, 3), dtype=np.uint8) * 128
    mask = np.zeros((512, 512), dtype=np.uint8)
    mask[100:200, 100:200] = 255  # only top-left quarter is foreground

    agent = FeatureExtractionAgent(embed_fn=_capturing_embed)
    result = await agent.run(FeatureInput(image=image, mask=mask))
    assert result.ok is True
    # Pixels outside mask should be zero
    outside = calls[0][300, 300]
    assert all(c == 0 for c in outside)


@pytest.mark.asyncio
async def test_bad_embedding_shape_fails():
    def _bad_embed(_: np.ndarray) -> np.ndarray:
        return np.zeros((512, 2), dtype=np.float32)  # wrong shape

    agent = FeatureExtractionAgent(embed_fn=_bad_embed)
    result = await agent.run(FeatureInput(image=_random_image()))
    assert result.ok is False


@pytest.mark.asyncio
async def test_non_normalised_embedding_fails():
    def _unnorm_embed(_: np.ndarray) -> np.ndarray:
        return np.ones(512, dtype=np.float32) * 10.0  # norm >> 1

    agent = FeatureExtractionAgent(embed_fn=_unnorm_embed)
    result = await agent.run(FeatureInput(image=_random_image()))
    assert result.ok is False


@pytest.mark.asyncio
async def test_none_mask_uses_full_image():
    received: list[np.ndarray] = []

    def _capture(img: np.ndarray) -> np.ndarray:
        received.append(img.copy())
        vec = np.ones(512, dtype=np.float32)
        return vec / np.linalg.norm(vec)

    image = np.ones((512, 512, 3), dtype=np.uint8) * 99
    agent = FeatureExtractionAgent(embed_fn=_capture)
    await agent.run(FeatureInput(image=image, mask=None))
    assert np.array_equal(received[0], image)
