"""Admin routes — yönetim işlemleri."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.feature_extraction_agent import FeatureExtractionAgent, FeatureInput
from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput
from core.database import get_session
from core.dependencies import feature_extraction_agent, preprocessing_agent
from models.db import Photo
from repositories.photo_repository import PhotoRepository

router = APIRouter(prefix="/admin", tags=["admin"])


class ReembedResult(BaseModel):
    total: int
    success: int
    failed: int
    skipped: int


@router.post("/reembed", response_model=ReembedResult, summary="Tüm fotoğrafları yeniden göm")
async def reembed_all(
    session: AsyncSession = Depends(get_session),
    preproc: ImagePreprocessingAgent = Depends(preprocessing_agent),
    feat_ext: FeatureExtractionAgent = Depends(feature_extraction_agent),
) -> ReembedResult:
    """Tüm fotoğrafları diskten okuyup tam pipeline ile (ön işleme + 3-bölge gömme) yeniden gömer.

    UPLOAD ile aynı pipeline kullanıldığı için query ve stored embedding aynı uzayda olur.
    """
    result = await session.execute(select(Photo))
    photos: list[Photo] = list(result.scalars().all())

    total = len(photos)
    success = failed = skipped = 0

    for photo in photos:
        # Dosyayı disk üzerinde bul
        from pathlib import Path
        path = Path(photo.file_path)
        if not path.exists():
            alt = Path("uploads") / photo.file_path
            if alt.exists():
                path = alt
            else:
                skipped += 1
                continue

        try:
            image_bytes = path.read_bytes()

            # Aşama 1 — Tam pipeline ön işleme (CLAHE + 3 bölge tespiti)
            on_isleme = await preproc.run(
                PreprocessingInput(image_bytes=image_bytes, region="body")
            )
            if not on_isleme.ok:
                failed += 1
                continue

            on = on_isleme.value

            # Aşama 2 — 3 bölge ağırlıklı gömme (0.30 kafa + 0.50 karapaks + 0.20 gövde)
            ozellik = await feat_ext.run(
                FeatureInput(
                    image=on.normalised,
                    mask=on.segmentation.mask,
                    region_head=on.region_head,
                    region_carapace=on.region_carapace,
                    region_body=on.region_body,
                )
            )
            if not ozellik.ok:
                failed += 1
                continue

            embedding = ozellik.value.embedding

            # Aşama 3 — DB'ye yaz
            from sqlalchemy import text
            vec_str = f"'[{','.join(str(float(x)) for x in embedding.tolist())}]'"
            await session.execute(
                text(f"UPDATE photos SET embedding = {vec_str}::vector WHERE id = :id"),
                {"id": str(photo.id)},
            )
            success += 1

        except Exception:
            failed += 1

    await session.commit()
    return ReembedResult(total=total, success=success, failed=failed, skipped=skipped)
