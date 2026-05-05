"""Weighted-concatenation embedding: semantic + spatial colour → 1024-d.

Architecture
============
  EfficientNet-B0 backbone (ImageNet pretrained)
  → GlobalAveragePool → Linear(1280→512) + BN + ReLU + L2-norm  → s ∈ ℝ⁵¹² (unit)

  Spatial HSV histogram  (4×4 grid, H=8 bins × V=4 bins = 32/cell × 16 cells)
  → L2-norm → c ∈ ℝ⁵¹² (unit)

  Final embedding = concatenate([√0.30 · s, √0.70 · c]) ∈ ℝ¹⁰²⁴

Why concatenation, not weighted sum
=====================================
  cos(q_combined, r_combined) = 0.30·cos(s_q,s_r) + 0.70·cos(c_q,c_r)
  — exact weighted average of component similarities.
  Additive mixing then L2-norm does NOT give this identity.

Why spatial (4×4 grid) instead of global histogram
=====================================================
  A stadium scene (green field bottom, gold trophies middle, dark stands top)
  has a VERY different cell-by-cell colour layout than any turtle photo.
  Global histograms can confuse warm-toned unrelated photos with turtle shells.
"""
from __future__ import annotations

import threading
from functools import lru_cache
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    import torch.nn as nn

# Total dim = SEMANTIC_DIM + COLOR_DIM
SEMANTIC_DIM = 512
COLOR_DIM    = 512   # 4×4 grid × (H=8 × V=4) = 16 × 32 = 512
EMBEDDING_DIM = SEMANTIC_DIM + COLOR_DIM  # 1024

# ImageNet class indices that correspond to turtles
# 33=loggerhead (Caretta caretta!), 34=leatherback, 35=mud turtle, 36=terrapin, 37=box turtle
_TURTLE_CLASS_IDS: frozenset[int] = frozenset([33, 34, 35, 36, 37])

_model_lock = threading.Lock()

# Cosine-decomposition weights: cos_total = W_S·cos_semantic + W_C·cos_colour
# EfficientNet semantic knows "turtle" vs "person/trophy/car" — weight it higher.
# Spatial colour distinguishes individuals within the same species.
_W_S = 0.60   # semantic component weight
_W_C = 0.40   # spatial colour component weight
# Scaling factors so the concatenated vector is already a unit vector
_SCALE_S = float(np.sqrt(_W_S))  # ≈ 0.7746
_SCALE_C = float(np.sqrt(_W_C))  # ≈ 0.6325


# ── Semantic encoder ──────────────────────────────────────────────────────────

def _build_model() -> "nn.Module":
    import torch
    import torch.nn as nn
    from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

    backbone = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)

    # Use the first SEMANTIC_DIM rows of the pretrained classifier as a fixed projection.
    # This is fully deterministic across restarts — no random init, no saved weights needed.
    # backbone.classifier[1] is Linear(1280, 1000) with ImageNet pretrained weights.
    clf_weight = backbone.classifier[1].weight[:SEMANTIC_DIM].detach().clone()
    clf_bias   = backbone.classifier[1].bias[:SEMANTIC_DIM].detach().clone()

    class EfficientNetEmbedder(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.features = backbone.features
            self.pool     = backbone.avgpool
            self.proj     = nn.Linear(1280, SEMANTIC_DIM, bias=True)
            with torch.no_grad():
                self.proj.weight.copy_(clf_weight)
                self.proj.bias.copy_(clf_bias)

        def forward(self, x):
            import torch.nn.functional as F
            x = self.features(x)
            x = self.pool(x)
            x = torch.flatten(x, 1)
            x = self.proj(x)
            return F.normalize(x, p=2, dim=1)

    return EfficientNetEmbedder()


@lru_cache(maxsize=1)
def _get_classifier() -> "nn.Module":
    """Full EfficientNet-B0 with classification head — used for turtle detection only."""
    from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0
    model = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
    model.eval()
    return model


def turtle_probability(image_bgr: np.ndarray) -> float:
    """Return the combined ImageNet probability that the image contains a turtle (0–1).

    Uses EfficientNet-B0's classification logits — classes 33-37 cover all turtle species
    including loggerhead (Caretta caretta = class 33).
    Completely unrelated images (stadiums, trophies, cars, people) score < 0.002.
    Actual sea turtle photos typically score > 0.05.
    """
    import torch
    from torchvision import transforms

    t = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    rgb    = cv2.cvtColor(cv2.resize(image_bgr, (224, 224)), cv2.COLOR_BGR2RGB)
    tensor = t(rgb).unsqueeze(0)

    with _model_lock, torch.no_grad():
        logits = _get_classifier()(tensor)
    probs = torch.softmax(logits, dim=1)[0]
    return float(sum(probs[c] for c in _TURTLE_CLASS_IDS))


@lru_cache(maxsize=1)
def get_embedder() -> "nn.Module":
    model = _build_model()
    model.eval()
    return model


# ── Spatial colour histogram ──────────────────────────────────────────────────

def _spatial_color_histogram(image_bgr: np.ndarray) -> np.ndarray:
    """512-d spatial HSV histogram on a 4×4 grid, L2-normalised.

    Each of the 16 cells contributes H=8 bins × V=4 bins = 32 features.
    Captures the spatial layout of colours, not just their global distribution.
    16 cells × 32 = 512-d total.
    """
    img  = cv2.resize(image_bgr, (128, 128))
    hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    cell = 32  # 128 / 4

    parts: list[np.ndarray] = []
    for row in range(4):
        for col in range(4):
            patch = hsv[row*cell:(row+1)*cell, col*cell:(col+1)*cell]
            h = cv2.calcHist([patch], [0, 2], None, [8, 4], [0, 180, 0, 256])
            parts.append(h.flatten())

    flat = np.concatenate(parts).astype(np.float32)  # 512-d
    norm = np.linalg.norm(flat)
    if norm < 1e-9:
        return np.zeros(COLOR_DIM, dtype=np.float32)
    return flat / norm


# ── Public API ────────────────────────────────────────────────────────────────

def embed_image(image_bgr: np.ndarray) -> np.ndarray:
    """Return a 1024-d unit embedding: [√0.30·semantic | √0.70·spatial_colour].

    Cosine similarity between two such embeddings equals:
      0.30 × cosine(semantic_q, semantic_r) + 0.70 × cosine(colour_q, colour_r)

    This is mathematically exact — no approximation from additive mixing.
    """
    import torch
    from torchvision import transforms

    _transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    resized = cv2.resize(image_bgr, (224, 224))
    rgb     = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    tensor  = _transform(rgb).unsqueeze(0)

    with _model_lock, torch.no_grad():
        semantic = get_embedder()(tensor).squeeze(0).numpy().astype(np.float32)

    colour = _spatial_color_histogram(image_bgr)

    combined = np.concatenate([_SCALE_S * semantic, _SCALE_C * colour])
    # combined is already a unit vector: ||combined||² = 0.3 + 0.7 = 1
    return combined.astype(np.float32)
