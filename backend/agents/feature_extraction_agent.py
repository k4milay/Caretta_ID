"""FeatureExtractionAgent — ön işlenmiş görüntüden 512 boyutlu gömme vektörü üretir.

Giriş : FeatureInput  (PreprocessingAgent'tan normalleştirilmiş görüntü + bölgeler)
Çıkış : FeatureOutput (ağırlıklı birleşik gömme vektörü, boyut, model sürümü)

Üç bölge ağırlıklandırması:
  - Baş/yüz lekeleri  : %30 ağırlık  (bireysel tanımlama için önemli)
  - Karapaks deseni   : %50 ağırlık  (en ayırt edici özellik)
  - Genel vücut şekli : %20 ağırlık  (destekleyici bağlam)

Gömme fonksiyonu constructor'da enjekte edilir — testler PyTorch yüklemeden
deterministik sahte fonksiyon kullanabilir.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from services.embedding_model import EMBEDDING_DIM, embed_image

from .base_agent import BaseAgent

# Bölge ağırlıkları — toplam 1.0 olmalı
_AGIRLIK_BAS = 0.30       # Baş/yüz lekeleri ağırlığı
_AGIRLIK_KARAPAKS = 0.50  # Karapaks/kabuk deseni ağırlığı
_AGIRLIK_VUCUT = 0.20     # Genel vücut şekli ağırlığı

EmbedFn = Callable[[np.ndarray], np.ndarray]


@dataclass
class FeatureInput:
    """Özellik çıkarım ajanı için giriş verisi."""
    image: np.ndarray             # Tam normalleştirilmiş görüntü
    mask: np.ndarray | None = None
    # Üç anatomik bölge (PreprocessingAgent tarafından sağlanır)
    region_head: np.ndarray | None = None      # Baş bölgesi
    region_carapace: np.ndarray | None = None  # Karapaks bölgesi
    region_body: np.ndarray | None = None      # Tam vücut


@dataclass
class FeatureOutput:
    """Özellik çıkarım ajanı çıkış verisi."""
    embedding: np.ndarray
    dim: int = field(init=False)
    model_version: str = "efficientnet-b0-v2-ucbolge"

    def __post_init__(self) -> None:
        # Gömme boyutunu otomatik hesapla
        self.dim = len(self.embedding)


class FeatureExtractionAgent(BaseAgent[FeatureInput, FeatureOutput]):
    """Üç bölge ağırlıklı gömme vektörü üreten özellik çıkarım ajanı."""

    name = "OzellikCikarimi"

    def __init__(self, embed_fn: EmbedFn = embed_image) -> None:
        super().__init__()
        self._embed = embed_fn

    async def _execute(self, payload: FeatureInput) -> FeatureOutput:
        # Tüm üç bölge mevcutsa ağırlıklı birleşik gömme hesapla
        if self._uc_bolge_mevcut(payload):
            embedding = self._agirlikli_gomme_hesapla(payload)
        else:
            # Geriye dönük uyumluluk: sadece tek görüntü varsa
            goruntu = self._maskeyi_uygula(payload.image, payload.mask)
            embedding = self._embed(goruntu)

        # Gömme vektörünü doğrula
        self._gommeyi_dogrula(embedding)
        return FeatureOutput(embedding=embedding)

    # ------------------------------------------------------------------ Yardımcı metodlar

    def _uc_bolge_mevcut(self, payload: FeatureInput) -> bool:
        """Üç bölgenin de mevcut olup olmadığını kontrol eder."""
        return (
            payload.region_head is not None
            and payload.region_carapace is not None
            and payload.region_body is not None
        )

    def _agirlikli_gomme_hesapla(self, payload: FeatureInput) -> np.ndarray:
        """
        Üç bölgeden ayrı gömme vektörleri hesaplar ve ağırlıklı olarak birleştirir.

        Formül: v = 0.30*v_baş + 0.50*v_karapaks + 0.20*v_vücut
        Sonuç L2-normalize edilerek birim küre üzerinde konumlandırılır.
        """
        # Her bölge için ayrı gömme vektörü hesapla
        v_bas = self._embed(payload.region_head).astype(np.float64)
        v_karapaks = self._embed(payload.region_carapace).astype(np.float64)
        v_vucut = self._embed(payload.region_body).astype(np.float64)

        # Ağırlıklı doğrusal kombinasyon
        birlesik = (
            _AGIRLIK_BAS * v_bas
            + _AGIRLIK_KARAPAKS * v_karapaks
            + _AGIRLIK_VUCUT * v_vucut
        )

        # L2-normalize — kosinüs benzerliği için birim vektör gerekli
        norm = np.linalg.norm(birlesik)
        if norm < 1e-9:
            # Sıfır vektör durumu (çok nadir) — düzgün vektöre geri dön
            return v_vucut.astype(np.float32)

        return (birlesik / norm).astype(np.float32)

    def _maskeyi_uygula(self, goruntu: np.ndarray, maske: np.ndarray | None) -> np.ndarray:
        """Maske varsa arka plan piksellerini sıfırlar."""
        if maske is None or not maske.any():
            return goruntu
        # Arka plan piksellerini sıfırla — model spot bölgelerine odaklanır
        maskelenmis = goruntu.copy()
        maskelenmis[maske == 0] = 0
        return maskelenmis

    def _gommeyi_dogrula(self, vec: np.ndarray) -> None:
        """Gömme vektörünün boyut ve normalleşme gereksinimlerini doğrular."""
        if vec.ndim != 1 or len(vec) < 128:
            raise ValueError(
                f"Geçersiz gömme şekli: {vec.shape}. 1-B ve ≥128 boyut bekleniyor."
            )
        norm = float(np.linalg.norm(vec))
        if not (0.9 <= norm <= 1.1):
            raise ValueError(
                f"Gömme L2-normalize değil (norm={norm:.4f}). Beklenen: ~1.0"
            )
