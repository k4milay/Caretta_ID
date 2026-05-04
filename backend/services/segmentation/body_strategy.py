"""Body segmentation strategy — uses the full image as the region of interest.

For full-body photos the entire frame is already the subject. This strategy
returns the image unchanged with an all-foreground mask so the rest of the
pipeline treats every pixel as relevant.
"""
from __future__ import annotations

import numpy as np

from .base import SegmentationResult, SegmentationStrategy


class BodySegmentationStrategy(SegmentationStrategy):
    region_name = "body"

    def segment(self, image: np.ndarray) -> SegmentationResult:
        full_mask = np.full(image.shape[:2], 255, dtype=np.uint8)
        return SegmentationResult(roi=image, mask=full_mask, region_name=self.region_name)
