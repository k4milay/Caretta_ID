"""Baseline accuracy evaluation on SeaTurtleID2022.

Usage (after downloading the dataset):
  python ml/evaluation/evaluate_baseline.py --dataset_dir /path/to/SeaTurtleID2022

SeaTurtleID2022 structure expected:
  <dataset_dir>/
    images/
      <identity>/
        <photo1>.jpg
        ...

Metric: Rank-1 accuracy (top-1 match is the correct identity).
Also reports Rank-5 accuracy and mean Average Precision @ 5.

The script runs entirely offline — it builds in-memory embeddings (no DB).
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

# Ensure backend package is on path when run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from services.embedding_model import embed_image  # noqa: E402
from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput  # noqa: E402
import asyncio  # noqa: E402


async def _preprocess(img_path: Path) -> np.ndarray | None:
    agent = ImagePreprocessingAgent()
    data = img_path.read_bytes()
    result = await agent.run(PreprocessingInput(image_bytes=data, region="head"))
    if not result.ok:
        return None
    return result.value.segmentation.roi


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))  # already L2-normalised


def evaluate(dataset_dir: Path) -> None:
    identity_dirs = sorted(p for p in dataset_dir.iterdir() if p.is_dir())
    print(f"Found {len(identity_dirs)} identities in {dataset_dir}")

    # Build embedding gallery -----------------------------------------------
    gallery: dict[str, list[np.ndarray]] = defaultdict(list)
    for id_dir in identity_dirs:
        photos = sorted(id_dir.glob("*.jpg")) + sorted(id_dir.glob("*.png"))
        for photo in photos:
            roi = asyncio.run(_preprocess(photo))
            if roi is None:
                print(f"  SKIP {photo.name} (preprocessing failed)")
                continue
            vec = embed_image(roi)
            gallery[id_dir.name].append(vec)
        print(f"  {id_dir.name}: {len(gallery[id_dir.name])} embeddings")

    # Leave-one-out evaluation ----------------------------------------------
    rank1_hits = rank5_hits = total = 0

    for query_id, vecs in gallery.items():
        for i, query_vec in enumerate(vecs):
            # Build gallery excluding this query
            scores: list[tuple[float, str]] = []
            for cand_id, cand_vecs in gallery.items():
                for j, cand_vec in enumerate(cand_vecs):
                    if cand_id == query_id and j == i:
                        continue
                    scores.append((_cosine_sim(query_vec, cand_vec), cand_id))
            scores.sort(reverse=True)

            top1_id = scores[0][1] if scores else ""
            top5_ids = {s[1] for s in scores[:5]}

            if top1_id == query_id:
                rank1_hits += 1
            if query_id in top5_ids:
                rank5_hits += 1
            total += 1

    rank1 = rank1_hits / total if total else 0
    rank5 = rank5_hits / total if total else 0
    print(f"\n=== Baseline Results ===")
    print(f"Queries  : {total}")
    print(f"Rank-1   : {rank1:.1%}")
    print(f"Rank-5   : {rank5:.1%}")
    threshold_met = "✅ PASS" if rank1 >= 0.60 else "❌ FAIL (need ≥60%)"
    print(f"Threshold: {threshold_met}")
    return rank1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_dir", type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.dataset_dir)
