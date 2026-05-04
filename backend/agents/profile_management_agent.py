"""ProfileManagementAgent — kaplumbağa profillerinin ve fotoğrafların yaşam döngüsünü yönetir.

Sorumluluklar:
  Kaplumbağa kayıtlarını oluştur/oku/güncelle/sil ve fotoğrafları ilişkilendir.
  Fotoğraf eklendiğinde, vektör indeksi otomatik senkronize kalsın diye
  önce ön işlemden geçirilir, sonra 3-bölge ağırlıklı gömme vektörü üretilir.

Giriş : ProfileAction  (alt eylemler ayrışık birleşim)
Çıkış : ProfileResult  (eyleme eşleşen tipli sonuç)
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from agents.base_agent import BaseAgent
from agents.feature_extraction_agent import FeatureExtractionAgent, FeatureInput
from agents.preprocessing_agent import ImagePreprocessingAgent, PreprocessingInput
from models.db import Photo, Turtle
from repositories.photo_repository import PhotoRepository
from repositories.turtle_repository import TurtleRepository

# Fotoğraf yükleme dizini — ortam değişkeninden veya varsayılan
_UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))


# ── Alt eylem veri sınıfları ───────────────────────────────────────────────────

@dataclass
class AddPhotoAction:
    """Kaplumbağa profiline fotoğraf ekleme eylemi."""
    kind: Literal["add_photo"] = field(default="add_photo", init=False)
    turtle_id: uuid.UUID
    image_bytes: bytes
    region: str = "body"  # Varsayılan: tam vücut tespiti


@dataclass
class RegisterTurtleAction:
    """Yeni kaplumbağa kaydı oluşturma eylemi."""
    kind: Literal["register"] = field(default="register", init=False)
    name: str
    notes: str | None = None


@dataclass
class UpdateTurtleAction:
    """Mevcut kaplumbağa profilini güncelleme eylemi."""
    kind: Literal["update"] = field(default="update", init=False)
    turtle_id: uuid.UUID
    name: str | None = None
    notes: str | None = None


@dataclass
class DeleteTurtleAction:
    """Kaplumbağa profilini silme eylemi."""
    kind: Literal["delete"] = field(default="delete", init=False)
    turtle_id: uuid.UUID


# Ayrışık birleşim tipi — tip güvenli eylem gönderimi için
ProfileAction = RegisterTurtleAction | UpdateTurtleAction | DeleteTurtleAction | AddPhotoAction


# ── Sonuç tipleri ─────────────────────────────────────────────────────────────

@dataclass
class ProfileResult:
    """Profil yönetim eylemi sonucu."""
    turtle: Turtle | None = None
    photo: Photo | None = None
    deleted: bool = False
    message: str = ""


# ── Ajan ──────────────────────────────────────────────────────────────────────

class ProfileManagementAgent(BaseAgent[ProfileAction, ProfileResult]):
    """Kaplumbağa profili ve fotoğraf yaşam döngüsünü yöneten ajan."""

    name = "ProfilYonetimi"

    def __init__(
        self,
        turtle_repo: TurtleRepository,
        photo_repo: PhotoRepository,
        preprocessing: ImagePreprocessingAgent,
        feature_extraction: FeatureExtractionAgent,
    ) -> None:
        super().__init__()
        self._turtles = turtle_repo
        self._photos = photo_repo
        self._preprocessing = preprocessing
        self._feature_extraction = feature_extraction

    async def _execute(self, payload: ProfileAction) -> ProfileResult:
        """Eylem tipine göre doğru metodu çağırır."""
        if isinstance(payload, RegisterTurtleAction):
            return await self._kaydet(payload)
        if isinstance(payload, UpdateTurtleAction):
            return await self._guncelle(payload)
        if isinstance(payload, DeleteTurtleAction):
            return await self._sil(payload)
        if isinstance(payload, AddPhotoAction):
            return await self._fotograf_ekle(payload)
        raise TypeError(f"Bilinmeyen eylem tipi: {type(payload)}")

    async def _kaydet(self, eylem: RegisterTurtleAction) -> ProfileResult:
        """Yeni kaplumbağa profilini veritabanına kaydeder."""
        kaplumbaga = await self._turtles.create(name=eylem.name, notes=eylem.notes)
        return ProfileResult(
            turtle=kaplumbaga,
            message=f"'{kaplumbaga.name}' kaydedildi (id={kaplumbaga.id})"
        )

    async def _guncelle(self, eylem: UpdateTurtleAction) -> ProfileResult:
        """Mevcut kaplumbağa profilini günceller."""
        kaplumbaga = await self._turtles.get_by_id(eylem.turtle_id)
        if not kaplumbaga:
            raise ValueError(f"Kaplumbağa bulunamadı: {eylem.turtle_id}")
        if eylem.name:
            kaplumbaga.name = eylem.name
        if eylem.notes is not None:
            kaplumbaga.notes = eylem.notes
        # Oturumu kaydet ve nesneyi yenile
        await self._turtles._session.commit()
        await self._turtles._session.refresh(kaplumbaga)
        return ProfileResult(turtle=kaplumbaga, message="Profil güncellendi.")

    async def _sil(self, eylem: DeleteTurtleAction) -> ProfileResult:
        """Kaplumbağa ve ilişkili tüm kayıtları siler."""
        silindi = await self._turtles.delete(eylem.turtle_id)
        if not silindi:
            raise ValueError(f"Kaplumbağa bulunamadı: {eylem.turtle_id}")
        return ProfileResult(deleted=True, message="Kaplumbağa ve tüm ilişkili kayıtlar silindi.")

    async def _fotograf_ekle(self, eylem: AddPhotoAction) -> ProfileResult:
        """
        Fotoğrafı ekler: ön işleme → 3 bölge gömme → dosya kaydet → DB yaz.

        Senkron gömme: fotoğraf anında aranabilir olur; arka plan kuyruğu gerekmez.
        Yüksek trafikte Celery/ARQ'ya taşınabilir.
        """
        # Kaplumbağanın varlığını doğrula
        kaplumbaga = await self._turtles.get_by_id(eylem.turtle_id)
        if not kaplumbaga:
            raise ValueError(f"Kaplumbağa bulunamadı: {eylem.turtle_id}")

        # Aşama 1 — Görüntü ön işleme ve 3 bölge tespiti
        on_isleme = await self._preprocessing.run(
            PreprocessingInput(image_bytes=eylem.image_bytes, region=eylem.region)
        )
        if not on_isleme.ok:
            raise RuntimeError(f"Ön işleme başarısız: {on_isleme.error}")

        on = on_isleme.value

        # Aşama 2 — Üç bölge ağırlıklı gömme vektörü üretimi
        ozellik = await self._feature_extraction.run(
            FeatureInput(
                image=on.normalised,
                mask=on.segmentation.mask,
                region_head=on.region_head,
                region_carapace=on.region_carapace,
                region_body=on.region_body,
            )
        )
        if not ozellik.ok:
            raise RuntimeError(f"Gömme başarısız: {ozellik.error}")

        # Aşama 3 — Dosyayı diske kaydet
        dosya_yolu = self._dosya_kaydet(eylem.turtle_id, eylem.image_bytes)

        # Aşama 4 — Veritabanına kayıt ve gömme vektörünü güncelle
        fotograf = await self._photos.create(
            turtle_id=eylem.turtle_id, file_path=str(dosya_yolu)
        )
        await self._photos.upsert_embedding(fotograf.id, ozellik.value.embedding)

        return ProfileResult(
            photo=fotograf,
            message=f"Fotoğraf {fotograf.id} eklendi ve gömme vektörü güncellendi."
        )

    def _dosya_kaydet(self, kaplumbaga_id: uuid.UUID, veri: bytes) -> Path:
        """Fotoğraf baytlarını kaplumbağa klasörüne JPEG olarak kaydeder."""
        # Kaplumbağa için alt klasör oluştur
        hedef_klasor = _UPLOAD_DIR / str(kaplumbaga_id)
        hedef_klasor.mkdir(parents=True, exist_ok=True)
        # Benzersiz dosya adı üret
        hedef = hedef_klasor / f"{uuid.uuid4()}.jpg"
        hedef.write_bytes(veri)
        return hedef
