"""ArcFace metric-learning fine-tuning on SeaTurtleID2022.

Trains the EfficientNet-B0 projection head with ArcFace loss.
The backbone is frozen for the first N_WARMUP_EPOCHS, then unfrozen
for full fine-tuning at a smaller learning rate.

Usage:
  python ml/training/train_arcface.py --dataset_dir /path/to/SeaTurtleID2022

Output: ml/models/efficientnet_head.pt  (projection head state dict only)

Why ArcFace:
  - Explicitly optimises for inter-class separation on the unit hypersphere
  - Outperforms triplet loss on small re-ID datasets (fewer hyperparameters)
  - Inference is a simple L2-normalised forward pass (no special loss at test time)
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import EfficientNet_B0_Weights

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from services.embedding_model import EMBEDDING_DIM, EfficientNetEmbedder  # noqa: E402

_WEIGHTS_PATH = Path(__file__).parent.parent / "models" / "efficientnet_head.pt"
N_WARMUP_EPOCHS = 5
N_TOTAL_EPOCHS = 30
BATCH_SIZE = 32
LR_HEAD = 1e-3
LR_BACKBONE = 1e-4
ARC_SCALE = 64.0
ARC_MARGIN = 0.5


class TurtleDataset(Dataset):
    _transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    def __init__(self, dataset_dir: Path) -> None:
        import cv2
        self._samples: list[tuple[torch.Tensor, int]] = []
        self.classes: list[str] = []
        for label, id_dir in enumerate(sorted(d for d in dataset_dir.iterdir() if d.is_dir())):
            self.classes.append(id_dir.name)
            for img_path in id_dir.glob("*.jpg"):
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                tensor = self._transform(rgb)
                self._samples.append((tensor, label))

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, idx: int):
        return self._samples[idx]


class ArcFaceHead(nn.Module):
    def __init__(self, in_features: int, n_classes: int) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.empty(n_classes, in_features))
        nn.init.xavier_uniform_(self.weight)
        self.scale = ARC_SCALE
        self.margin = ARC_MARGIN

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        cos_theta = F.linear(embeddings, F.normalize(self.weight))
        cos_theta = cos_theta.clamp(-1.0, 1.0)
        theta = torch.acos(cos_theta)
        target_mask = torch.zeros_like(cos_theta).scatter_(1, labels.unsqueeze(1), 1.0)
        margined = torch.cos(theta + self.margin)
        logits = self.scale * (target_mask * margined + (1 - target_mask) * cos_theta)
        return F.cross_entropy(logits, labels)


def train(dataset_dir: Path) -> None:
    dataset = TurtleDataset(dataset_dir)
    n_classes = len(dataset.classes)
    print(f"Classes: {n_classes}, Samples: {len(dataset)}")

    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, drop_last=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model = EfficientNetEmbedder().to(device)
    arc_head = ArcFaceHead(EMBEDDING_DIM, n_classes).to(device)

    # Warm-up: train only projection head
    for param in model.features.parameters():
        param.requires_grad = False

    optimizer = torch.optim.AdamW(
        list(model.projection.parameters()) + list(arc_head.parameters()), lr=LR_HEAD
    )

    for epoch in range(N_TOTAL_EPOCHS):
        if epoch == N_WARMUP_EPOCHS:
            for param in model.features.parameters():
                param.requires_grad = True
            optimizer.add_param_group({"params": model.features.parameters(), "lr": LR_BACKBONE})
            print("Backbone unfrozen — full fine-tuning starts")

        model.train()
        arc_head.train()
        total_loss = 0.0
        for imgs, labels in loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            embeddings = model(imgs)
            loss = arc_head(embeddings, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        print(f"Epoch {epoch+1:03d}/{N_TOTAL_EPOCHS}  loss={total_loss/len(loader):.4f}")

    _WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.projection.state_dict(), _WEIGHTS_PATH)
    print(f"Saved projection head to {_WEIGHTS_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_dir", type=Path, required=True)
    args = parser.parse_args()
    train(args.dataset_dir)
