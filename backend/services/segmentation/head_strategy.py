"""Head/face segmentation strategy for Caretta caretta.

Pipeline (v1 — classical CV, no trained detector required):
  1. Take the upper 55 % of the image — head appears here in standard
     dorsal/lateral field photos.
  2. Apply GrabCut initialised with a tight centre-strip rectangle to
     separate head from water/background.
  3. Return the ROI + a binary mask of the dark spot regions
     (adaptive thresholding on the V channel of HSV).

This module is intentionally self-contained.  Swap it for a YOLO-based
detector in v2 without touching any other code path.
"""
from __future__ import annotations

import cv2
import numpy as np

from .base import SegmentationResult, SegmentationStrategy

_HEAD_CROP_RATIO = 0.55
_GRABCUT_ITERS = 5
_MIN_SPOT_AREA_PX = 20


class HeadSegmentationStrategy(SegmentationStrategy):
    region_name = "head"

    def segment(self, image: np.ndarray) -> SegmentationResult:
        head_region = self._crop_head_band(image)
        fg_mask = self._grabcut_foreground(head_region)
        spot_mask = self._extract_spot_mask(head_region, fg_mask)
        return SegmentationResult(roi=head_region, mask=spot_mask, region_name=self.region_name)

    # ------------------------------------------------------------------
    def _crop_head_band(self, image: np.ndarray) -> np.ndarray:
        h = image.shape[0]
        cut = max(1, int(h * _HEAD_CROP_RATIO))
        return image[:cut, :]

    def _grabcut_foreground(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        margin_y, margin_x = max(1, h // 8), max(1, w // 8)
        rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        mask = np.zeros((h, w), np.uint8)
        try:
            cv2.grabCut(image, mask, rect, bgd_model, fgd_model, _GRABCUT_ITERS, cv2.GC_INIT_WITH_RECT)
        except cv2.error:
            return np.ones((h, w), np.uint8) * 255

        fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        return fg_mask

    def _extract_spot_mask(self, image: np.ndarray, fg_mask: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        v_channel = hsv[:, :, 2]

        # Adaptive threshold finds dark spots relative to local background
        spot_mask = cv2.adaptiveThreshold(
            v_channel, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=31, C=8,
        )

        # Keep only spots inside detected foreground
        combined = cv2.bitwise_and(spot_mask, fg_mask)

        # Remove specks smaller than a real spot
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)

        return combined
