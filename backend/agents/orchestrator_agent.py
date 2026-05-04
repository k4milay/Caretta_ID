"""OrchestratorAgent — tanımlama boru hattının tek giriş noktası.

Aşamaları sırayla bağlar:
  1. ImagePreprocessingAgent  — doğrula + normalleştir + tam vücut tespit + 3 bölge kırp
  2. FeatureExtractionAgent   — 3 bölge ağırlıklı gömme vektörü üret
  3. SimilaritySearchAgent    — pgvector'da ara, sıralı eşleşmeleri döndür

Her aşamanın AgentResult'ı devam etmeden önce kontrol edilir; hatalar
açık bir mesajla yüzeye çıkar ve çağırana istisna olarak yayılmaz.
Orkestratör kendisi de bir ajan olduğundan aynı zamanlama/loglama
altyapısına katılır.

HTTP katmanına sunulan temiz API yüzeyi: ``identify(image_bytes)``
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from models.schemas import IdentificationResponse
from .base_agent import BaseAgent, AgentResult
from .feature_extraction_agent import FeatureExtractionAgent, FeatureInput
from .preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput
from .similarity_search_agent import SimilarityInput, SimilaritySearchAgent

# Varsayılan eşik değeri — tam vücut + 3 bölge gömme için ayarlandı
_VARSAYILAN_ESIK = 0.78


@dataclass
class IdentifyInput:
    """Orkestratör ajanı için giriş verisi."""
    image_bytes: bytes
    region: str = "body"          # Varsayılan: tam vücut tespiti
    top_k: int = 5                # Döndürülecek maksimum eşleşme sayısı
    threshold: float = _VARSAYILAN_ESIK  # Minimum benzerlik eşiği
    exclude_photo_id: UUID | None = None


class OrchestratorAgent(BaseAgent[IdentifyInput, IdentificationResponse]):
    """Üç aşamalı tanımlama boru hattını yöneten orkestratör ajan."""

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
        # Aşama 1 — Görüntü ön işleme ve 3 bölge tespiti
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
            threshold=cikti.threshold,
            accepted=cikti.accepted,
        )

    @staticmethod
    def _basarili_mi(sonuc: AgentResult, asama: str) -> None:
        """Ajan sonucunun başarılı olup olmadığını kontrol eder; değilse hata fırlatır."""
        if not sonuc.ok:
            raise RuntimeError(f"{asama} aşaması başarısız: {sonuc.error}")
