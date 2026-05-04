"""ImagePreprocessingAgent — görüntüyü doğrular, normalleştirir ve tam vücut tespiti yapar.

Giriş : PreprocessingInput  (ham bayt + isteğe bağlı bölge ipucu)
Çıkış : PreprocessingOutput (normalleştirilmiş görüntü + segmentasyon sonucu)

Tek sorumluluk: ham yüklenen dosyayı özellik çıkarımı için hazır,
temiz bir numpy dizisine dönüştürmek. Tüm segmentasyon mantığı
enjekte edilen SegmentationStrategy içinde yaşar.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from services.segmentation.base import SegmentationResult, SegmentationStrategy
from services.segmentation.factory import get_strategy

from .base_agent import BaseAgent

# Sabitler ---------------------------------------------------------------
_MIN_KENAR_PX = 64                # Minimum kabul edilebilir görüntü boyutu
_MAX_BAYT = 20 * 1024 * 1024      # 20 MB dosya boyutu sınırı
_HEDEF_BOYUT = (224, 224)         # Model girişi için standart boyut
_GECERLI_SIHIRLI: dict[bytes, str] = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG":      "png",
    b"BM":           "bmp",
    b"RIFF":         "webp",
}


@dataclass
class PreprocessingInput:
    """Ön işleme ajanı için giriş verisi."""
    image_bytes: bytes
    region: str = "body"  # Varsayılan: tam vücut tespiti


@dataclass
class PreprocessingOutput:
    """Ön işleme ajanı çıkış verisi — normalleştirilmiş görüntü ve bölgeler."""
    normalised: np.ndarray          # Tam normalleştirilmiş görüntü (224x224)
    segmentation: SegmentationResult
    original_size: tuple[int, int]  # (Genişlik, Yükseklik)
    # Üç bölge kırpması — ağırlıklı embedding için kullanılır
    region_head: np.ndarray      # Baş bölgesi (%30 ağırlık)
    region_carapace: np.ndarray  # Karapaks/kabuk bölgesi (%50 ağırlık)
    region_body: np.ndarray      # Tüm vücut genel görünüm (%20 ağırlık)


class ImagePreprocessingAgent(BaseAgent[PreprocessingInput, PreprocessingOutput]):
    """Görüntüyü doğrulayan, normalleştiren ve tam vücut tespiti yapan ajan."""

    name = "GorüntuOnIsleme"

    def __init__(self, strategy: SegmentationStrategy | None = None) -> None:
        super().__init__()
        self._strategy = strategy

    async def _execute(self, payload: PreprocessingInput) -> PreprocessingOutput:
        # Dosya baytlarını doğrula
        self._baytlari_dogrula(payload.image_bytes)
        # Görüntüyü numpy dizisine çöz
        goruntu = self._coz(payload.image_bytes)
        orijinal_boyut = (goruntu.shape[1], goruntu.shape[0])  # (G, Y)
        # Minimum boyut kontrolü
        self._boyutu_dogrula(goruntu)

        # CLAHE ile kontrast normalleştirmesi
        normallestirilmis = self._normallesтir(goruntu)

        # Tam vücut tespiti ve bölge kırpmaları
        bas_bolgesi, karapaks_bolgesi, vucut_bolgesi = self._bolgeleri_kirp(normallestirilmis)

        # Segmentasyon stratejisini uygula (geriye dönük uyumluluk)
        strateji = self._strategy or get_strategy(payload.region)
        seg = strateji.segment(normallestirilmis)

        return PreprocessingOutput(
            normalised=normallestirilmis,
            segmentation=seg,
            original_size=orijinal_boyut,
            region_head=bas_bolgesi,
            region_carapace=karapaks_bolgesi,
            region_body=vucut_bolgesi,
        )

    # ------------------------------------------------------------------ Yardımcı metodlar

    def _baytlari_dogrula(self, veri: bytes) -> None:
        """Dosya baytlarının geçerliliğini kontrol eder."""
        if len(veri) == 0:
            raise ValueError("Boş görüntü verisi.")
        if len(veri) > _MAX_BAYT:
            raise ValueError(f"Görüntü {_MAX_BAYT // (1024*1024)} MB sınırını aşıyor.")
        baslik = veri[:4]
        if not any(baslik.startswith(sihir) for sihir in _GECERLI_SIHIRLI):
            raise ValueError("Desteklenmeyen format. Kabul edilen: JPEG, PNG, BMP, WebP.")

    def _coz(self, veri: bytes) -> np.ndarray:
        """Ham baytları OpenCV görüntü dizisine dönüştürür."""
        dizi = np.frombuffer(veri, dtype=np.uint8)
        goruntu = cv2.imdecode(dizi, cv2.IMREAD_COLOR)
        if goruntu is None:
            raise ValueError("Görüntü çözümlemesi başarısız — dosya bozuk olabilir.")
        return goruntu

    def _boyutu_dogrula(self, goruntu: np.ndarray) -> None:
        """Görüntünün minimum boyut gereksinimini karşıladığını doğrular."""
        y, g = goruntu.shape[:2]
        if y < _MIN_KENAR_PX or g < _MIN_KENAR_PX:
            raise ValueError(
                f"Görüntü çok küçük ({g}×{y}). Minimum {_MIN_KENAR_PX}px gerekli."
            )

    def _normallesтir(self, goruntu: np.ndarray) -> np.ndarray:
        """
        Görüntüyü hedef boyuta yeniden boyutlandırır ve CLAHE kontrast iyileştirmesi uygular.
        LAB renk uzayında L kanalına CLAHE — farklı aydınlatma koşullarında tutarlılık sağlar.
        """
        # Hedef boyuta yeniden boyutlandır
        yeniden_boyutlandirilmis = cv2.resize(
            goruntu, _HEDEF_BOYUT, interpolation=cv2.INTER_LANCZOS4
        )
        # LAB renk uzayına çevir — L kanalı parlaklığı temsil eder
        lab = cv2.cvtColor(yeniden_boyutlandirilmis, cv2.COLOR_BGR2LAB)
        # CLAHE ile parlaklık kanalını iyileştir
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        # BGR renk uzayına geri dön
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def _bolgeleri_kirp(
        self, goruntu: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Normalleştirilmiş görüntüden üç anatomik bölge kırpar.

        Bölge dağılımı (224x224 görüntü için):
          - Baş bölgesi   : üst %30 → satır 0-67    (%30 embedding ağırlığı)
          - Karapaks bölge: orta %50 → satır 67-179  (%50 embedding ağırlığı)
          - Vücut bölgesi : tüm görüntü              (%20 embedding ağırlığı)
        """
        y, g = goruntu.shape[:2]

        # Baş bölgesi — görüntünün üst %30'u (baş ve yüz lekeleri)
        bas_sinir = int(y * 0.30)
        bas = goruntu[:bas_sinir, :]
        bas = cv2.resize(bas, _HEDEF_BOYUT, interpolation=cv2.INTER_LANCZOS4)

        # Karapaks bölgesi — görüntünün orta %50'si (kabuk deseni)
        karapaks_ust = int(y * 0.20)
        karapaks_alt = int(y * 0.85)
        karapaks = goruntu[karapaks_ust:karapaks_alt, :]
        karapaks = cv2.resize(karapaks, _HEDEF_BOYUT, interpolation=cv2.INTER_LANCZOS4)

        # Vücut bölgesi — tüm görüntü (genel vücut şekli)
        vucut = goruntu.copy()

        return bas, karapaks, vucut
