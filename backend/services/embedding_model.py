"""EfficientNet-B0 + HSV color histogram combined embedding.

Architecture:
  EfficientNet-B0 backbone (ImageNet pretrained)
  → GlobalAveragePool (1280-d)
  → Linear(1280, 512) + BN + ReLU + L2-norm  → 512-d semantic vector

  HSV color histogram: H=32 bins × V=16 bins = 512-d → L2-norm

  Final: 0.60 × semantic + 0.40 × color → L2-norm → 512-d

Mixing color histogram makes visually distinct subjects (car vs turtle,
baby vs adult) produce meaningfully different embeddings even without
metric-learning fine-tuning.
"""
from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    import torch.nn as nn

EMBEDDING_DIM = 512
_WEIGHTS_PATH = Path("ml/models/efficientnet_head.pt")
_model_lock = threading.Lock()

# Mixing weights — semantic vs colour
_W_SEMANTIC = 0.60
_W_COLOR    = 0.40


def _build_model() -> "nn.Module":
    import torch.nn as nn
    from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

    backbone = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)

    class EfficientNetEmbedder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.features = backbone.features
            self.pool = backbone.avgpool
            self.projection = nn.Sequential(
                nn.Flatten(),
                nn.Linear(1280, EMBEDDING_DIM),
                nn.BatchNorm1d(EMBEDDING_DIM),
                nn.ReLU(inplace=True),
            )

        def forward(self, x):
            import torch.nn.functional as F
            x = self.features(x)
            x = self.pool(x)
            x = self.projection(x)
            return F.normalize(x, p=2, dim=1)

    return EfficientNetEmbedder()


@lru_cache(maxsize=1)
def get_embedder() -> "nn.Module":
    import torch
    model = _build_model()
    if _WEIGHTS_PATH.exists():
        state = torch.load(_WEIGHTS_PATH, map_location="cpu", weights_only=True)
        model.projection.load_state_dict(state)
    model.eval()
    return model


def _color_histogram(image_bgr: np.ndarray) -> np.ndarray:
    """512-d HSV color histogram (H=32 bins, V=16 bins), L2-normalised.

    Captures dominant colour distribution — highly discriminative for
    visually distinct subjects (car vs turtle, baby vs adult).
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    # H axis: 0-180, V axis: 0-256 → 32×16 = 512 bins
    hist = cv2.calcHist([hsv], [0, 2], None, [32, 16], [0, 180, 0, 256])
    flat = hist.flatten().astype(np.float32)
    norm = np.linalg.norm(flat)
    if norm < 1e-9:
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)
    return flat / norm


def embed_image(image_bgr: np.ndarray) -> np.ndarray:
    """512-d combined embedding: 60% EfficientNet semantic + 40% HSV colour.

    The colour component ensures visually unrelated images (e.g. a car vs a
    sea turtle) score well below the 0.84 acceptance threshold even when the
    deep network assigns similar category-level features.
    """
    import torch
    from torchvision import transforms

    _transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    tensor = _transform(rgb).unsqueeze(0)

    with _model_lock, torch.no_grad():
        semantic_vec = get_embedder()(tensor).squeeze(0).numpy().astype(np.float32)

    color_vec = _color_histogram(image_bgr)

    combined = _W_SEMANTIC * semantic_vec + _W_COLOR * color_vec
    norm = np.linalg.norm(combined)
    if norm < 1e-9:
        return semantic_vec
    return (combined / norm).astype(np.float32)
