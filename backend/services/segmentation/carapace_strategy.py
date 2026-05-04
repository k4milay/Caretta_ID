"""Carapace segmentation strategy — stub for future implementation.

Replace the body of ``segment`` with a trained scute-pattern detector when
carapace-based ID is required.  The rest of the pipeline (preprocessing agent,
feature extractor, repository) needs no changes.
"""
from __future__ import annotations

import numpy as np

from .base import SegmentationResult, SegmentationStrategy


class CarapaceSegmentationStrategy(SegmentationStrategy):
    region_name = "carapace"

    def segment(self, image: np.ndarray) -> SegmentationResult:
        raise NotImplementedError(
            "Carapace segmentation is not yet implemented. "
            "Implement a scute-pattern detector and replace this method."
        )
