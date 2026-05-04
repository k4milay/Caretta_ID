"""Abstract segmentation contract.

A SegmentationStrategy receives a normalised image (H×W×3, uint8, BGR) and
returns:
  - roi: the cropped region of interest (same dtype)
  - mask: binary uint8 mask aligned to *roi*, 255 = foreground spot area

Adding a new anatomical region (e.g. carapace) requires only a new subclass —
the preprocessing pipeline never needs to change (Open/Closed principle).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SegmentationResult:
    roi: np.ndarray
    mask: np.ndarray
    region_name: str


class SegmentationStrategy(ABC):
    region_name: str = "unknown"

    @abstractmethod
    def segment(self, image: np.ndarray) -> SegmentationResult:
        """Extract ROI and binary spot mask from a normalised image."""
