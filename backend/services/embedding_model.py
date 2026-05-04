"""EfficientNet-B0 embedding model.

Architecture:
  EfficientNet-B0 backbone (ImageNet pretrained)
  → GlobalAveragePool  (1280-d)
  → Linear(1280, 512) + BN + ReLU
  → L2-normalise  → 512-d unit hypersphere embedding

Metric-learning fine-tuning (ArcFace/triplet) happens in ml/training/.
torch/torchvision are imported lazily so this module is safe to import in
test environments without a GPU stack.
"""
from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import torch.nn as nn

EMBEDDING_DIM = 512
_WEIGHTS_PATH = Path("ml/models/efficientnet_head.pt")
_model_lock = threading.Lock()


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


def embed_image(image_bgr: np.ndarray) -> np.ndarray:
    """Return a 512-d L2-normalised numpy float32 vector."""
    import cv2
    import torch
    from torchvision import transforms

    _transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    tensor = _transform(rgb).unsqueeze(0)
    with _model_lock, torch.no_grad():
        vec = get_embedder()(tensor)
    return vec.squeeze(0).numpy().astype(np.float32)
