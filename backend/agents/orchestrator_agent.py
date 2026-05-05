"""OrchestratorAgent — tanımlama boru hattının tek giriş noktası.

Aşamaları sırayla bağlar:
  0. Kaplumbağa tespiti — EfficientNet ImageNet sınıflandırıcısı ile fotoğrafta
     kaplumbağa olup olmadığını kontrol et; yoksa sıfır sonuçla erken çık.
  1. ImagePreprocessingAgent  — doğrula + normalleştir + tam vücut tespit + 3 bölge kırp
  2. FeatureExtractionAgent   — 3 bölge ağırlıklı gömme vektörü üret
  3. SimilaritySearchAgent    — pgvector'da ara, sıralı eşleşmeleri döndür
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

import cv2
import numpy as np

from models.schemas import IdentificationResponse
from services.embedding_model import turtle_probability
from .base_agent import BaseAgent, AgentResult
from .feature_extraction_agent import FeatureExtractionAgent, FeatureInput
from .preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput
from .similarity_search_agent import SimilarityInput, SimilaritySearchAgent

_VARSAYILAN_ESIK = 0.70

# EfficientNet-B0 ImageNet sınıflandırması ile kaplumbağa tespiti için minimum olasılık.
# Kaplumbağa fotoğrafları tipik: %5-40 | Stadyum/araba/kişi: < %0.2
_KAPLUMBAGA_MIN_OLASILIK = 0.005  # %0.5


@dataclass
class IdentifyInput:
    """Orkestratör ajanı için giriş verisi."""
    image_bytes: bytes
    region: str = "body"
    top_k: int = 5
    threshold: float = _VARSAYILAN_ESIK
    exclude_photo_id: UUID | None = None


class OrchestratorAgent(BaseAgent[IdentifyInput, IdentificationResponse]):
    """Dört aşamalı tanımlama boru hattını yöneten orkestratör ajan."""

    name = "Orkestrator"

    def __init__(
        self,
        preprocessing: ImagePreprocessingAgent,
        feature_extraction: FeatureExtractionAgent,
        similarity_search: SimilaritySearchAgent,
    ) -> None:
        super().__init__()
        self._preprocessing = preprocessing
        self._feature_extraction = feature_extraction
        self._similarity_search = similarity_search

    async def _execute(self, payload: IdentifyInput) -> IdentificationResponse:
        # Aşama 0 — Kaplumbağa tespiti kapısı
        # EfficientNet-B0, ImageNet'te loggerhead (class 33 = Caretta caretta!) dahil
        # 5 kaplumbağa sınıfı biliyor. Kaplumbağa yoksa sıfır sonuçla dön.
        img_arr = cv2.imdecode(np.frombuffer(payload.image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img_arr is None:
            raise RuntimeError("Görüntü okunamadı.")

        kapumbaga_olasiligi = await asyncio.get_event_loop().run_in_executor(
            None, turtle_probability, img_arr
        )

        if kapumbaga_olasiligi < _KAPLUMBAGA_MIN_OLASILIK:
            return IdentificationResponse(
                matches=[],
                candidates=[],
                threshold=payload.threshold,
                accepted=False,
                turtle_detected=False,
            )

        # Aşama 1 — Görüntü ön işleme
        on_isleme_sonucu = await self._preprocessing.run(
            PreprocessingInput(image_bytes=payload.image_bytes, region=payload.region)
        )
        self._basarili_mi(on_isleme_sonucu, "GörüntüÖnİşleme")
        on = on_isleme_sonucu.value

        # Aşama 2 — Üç bölge ağırlıklı gömme vektörü üretimi
        ozellik_sonucu = await self._feature_extraction.run(
            FeatureInput(
                image=on.normalised,
                mask=on.segmentation.mask,
                region_head=on.region_head,
                region_carapace=on.region_carapace,
                region_body=on.region_body,
            )
        )
        self._basarili_mi(ozellik_sonucu, "ÖzellikÇıkarımı")
        gomme = ozellik_sonucu.value.embedding

        # Aşama 3 — pgvector benzerlik araması
        arama_sonucu = await self._similarity_search.run(
            SimilarityInput(
                embedding=gomme,
                top_k=payload.top_k,
                threshold=payload.threshold,
                exclude_photo_id=payload.exclude_photo_id,
            )
        )
        self._basarili_mi(arama_sonucu, "BenzerlikArama")

        cikti = arama_sonucu.value
        return IdentificationResponse(
            matches=cikti.matches,
            candidates=cikti.candidates,
            threshold=cikti.threshold,
            accepted=cikti.accepted,
        )

    @staticmethod
    def _basarili_mi(sonuc: AgentResult, asama: str) -> None:
        if not sonuc.ok:
            raise RuntimeError(f"{asama} aşaması başarısız: {sonuc.error}")
