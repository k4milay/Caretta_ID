"""Tests for segmentation strategy layer."""
import numpy as np
import pytest

from services.segmentation.carapace_strategy import CarapaceSegmentationStrategy
from services.segmentation.factory import get_strategy
from services.segmentation.head_strategy import HeadSegmentationStrategy


def _bgr(h: int = 512, w: int = 512) -> np.ndarray:
    return np.random.randint(30, 200, (h, w, 3), dtype=np.uint8)


def test_factory_returns_head_by_default():
    assert isinstance(get_strategy("head"), HeadSegmentationStrategy)


def test_factory_unknown_region_raises():
    with pytest.raises(ValueError, match="Unknown"):
        get_strategy("flipper")


def test_head_strategy_returns_correct_shape():
    strategy = HeadSegmentationStrategy()
    result = strategy.segment(_bgr())
    assert result.region_name == "head"
    assert result.roi.ndim == 3
    assert result.mask.ndim == 2
    assert result.roi.shape[:2] == result.mask.shape


def test_head_roi_height_is_upper_band():
    img = _bgr(h=512, w=512)
    result = HeadSegmentationStrategy().segment(img)
    # ROI height must be ≤ 55% of original (allowing +/- 1 rounding)
    assert result.roi.shape[0] <= int(512 * 0.56)


def test_carapace_strategy_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        CarapaceSegmentationStrategy().segment(_bgr())
