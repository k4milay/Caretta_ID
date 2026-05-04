"""
Sentetik kaplumbağa veri seti üretici.

Her kaplumbağa için benzersiz tam vücut desenleri oluşturur:
  - Baş bölgesi lekeleri (rastgele nokta deseni)
  - Karapaks deseni (altıgen/poligon ağı)
  - Vücut renk tonu (bireysel renk imzası)

Her kaplumbağa için 4 fotoğraf üretilir:
  - Farklı aydınlatma koşulları
  - Hafif açı değişimleri (döndürme ±10°)
  - Gürültü varyasyonları

Çıktı: data/sample_photos/<isim>/<isim>_<N>.jpg (224×224 JPEG)
"""
import json
import os
import random
import sys
from pathlib import Path

import cv2
import numpy as np

# Üretilecek kaplumbağa sayısı ve kaplumbağa başına fotoğraf
KAPLUMBAGA_SAYISI = 10
FOTOGRAF_SAYISI = 4
GORUNTU_BOYUTU = 224  # px — model giriş boyutu
KALITE = 90           # JPEG kalite yüzdesi

# Çıktı klasörü
CIKTI_DIZINI = Path(__file__).parent / "sample_photos"

# Rastgele tohum — tekrar üretilebilirlik için
TOHUM = 42
random.seed(TOHUM)
np.random.seed(TOHUM)

# Kaplumbağa isimleri (Türk mitolojisi ve deniz temalı)
ISIMLER = [
    "Athena", "Poseidon", "Tethys", "Nereid", "Triton",
    "Calypso", "Proteus", "Galene", "Thalassa", "Amphitrite",
]


def kaplumbaga_rengi_uret(indeks: int) -> tuple[int, int, int]:
    """Her kaplumbağa için benzersiz temel BGR renk tonu üretir."""
    # Kaplumbağa yeşil-kahve tonları arasında değişen renk
    np.random.seed(indeks * 137)  # Her kaplumbağa için sabit tohum
    yesil = int(np.random.randint(60, 130))
    kahve = int(np.random.randint(40, 90))
    sari = int(np.random.randint(30, 70))
    return (kahve, yesil, sari)  # BGR formatı


def vucut_cizimleri_yap(goruntu: np.ndarray, renk: tuple, leke_deseni: np.ndarray) -> np.ndarray:
    """Kaplumbağa tam vücut şeklini ve desenlerini görüntüye çizer."""
    y, x = goruntu.shape[:2]
    merkez_x, merkez_y = x // 2, y // 2

    # ── Vücut (oval) ──────────────────────────────────────────────────────
    r1, g1, b1 = renk
    # Ana vücut — koyu yeşil-kahve oval
    cv2.ellipse(goruntu, (merkez_x, merkez_y + 10), (75, 85), 0, 0, 360,
                (b1, g1, r1), -1)

    # ── Karapaks deseni (altıgen ağ) ──────────────────────────────────────
    karapaks_renk = (max(0, b1-20), max(0, g1-15), max(0, r1-20))
    cv2.ellipse(goruntu, (merkez_x, merkez_y + 5), (68, 76), 0, 0, 360,
                karapaks_renk, -1)

    # Karapaks üzerine altıgen benzeri çizgiler
    np.random.seed(int(leke_deseni[0] * 100))
    for i in range(-3, 4):
        for j in range(-3, 4):
            px = merkez_x + i * 22 + j * 8
            py = merkez_y + j * 22 + i * 4
            if 30 < px < x - 30 and 30 < py < y - 30:
                boyut = np.random.randint(8, 15)
                kayu = (min(255, b1+30), min(255, g1+20), min(255, r1+15))
                noktalar = []
                for k in range(6):
                    aci = k * 60
                    nx = int(px + boyut * np.cos(np.radians(aci)))
                    ny = int(py + boyut * np.sin(np.radians(aci)))
                    noktalar.append([nx, ny])
                cv2.polylines(goruntu, [np.array(noktalar)], True, kayu, 1)

    # ── Palet (ön yüzgeçler) ──────────────────────────────────────────────
    sol_palet = np.array([[merkez_x-75, merkez_y], [merkez_x-110, merkez_y-30],
                          [merkez_x-90, merkez_y+20]], np.int32)
    sag_palet = np.array([[merkez_x+75, merkez_y], [merkez_x+110, merkez_y-30],
                          [merkez_x+90, merkez_y+20]], np.int32)
    cv2.fillPoly(goruntu, [sol_palet], (b1, g1, r1))
    cv2.fillPoly(goruntu, [sag_palet], (b1, g1, r1))

    # ── Baş ───────────────────────────────────────────────────────────────
    bas_merkez = (merkez_x, merkez_y - 80)
    cv2.ellipse(goruntu, bas_merkez, (28, 22), 0, 0, 360, (b1+5, g1+5, r1+5), -1)

    # Baş üzerine bireysel leke deseni (tanımlama için kritik)
    for i, (lx, ly, lr) in enumerate(zip(
        leke_deseni[0::3], leke_deseni[1::3], leke_deseni[2::3]
    )):
        px = int(bas_merkez[0] + lx * 20 - 10)
        py = int(bas_merkez[1] + ly * 18 - 9)
        yaricap = int(lr * 4 + 2)
        leke_renk = (
            min(255, b1 + int(lx * 80)),
            min(255, g1 + int(ly * 40)),
            max(0, r1 - int(lr * 30)),
        )
        cv2.circle(goruntu, (px, py), yaricap, leke_renk, -1)

    # Gözler
    cv2.circle(goruntu, (bas_merkez[0]-10, bas_merkez[1]-5), 5, (20, 20, 20), -1)
    cv2.circle(goruntu, (bas_merkez[0]+10, bas_merkez[1]-5), 5, (20, 20, 20), -1)
    cv2.circle(goruntu, (bas_merkez[0]-9, bas_merkez[1]-6), 2, (255, 255, 255), -1)
    cv2.circle(goruntu, (bas_merkez[0]+11, bas_merkez[1]-6), 2, (255, 255, 255), -1)

    # Arka yüzgeç
    arka = np.array([[merkez_x-20, merkez_y+85], [merkez_x+20, merkez_y+85],
                     [merkez_x, merkez_y+110]], np.int32)
    cv2.fillPoly(goruntu, [arka], (b1, g1, r1))

    return goruntu


def varyasyon_uygula(goruntu: np.ndarray, varyasyon: int, aydınlatma_guc: float) -> np.ndarray:
    """
    Fotoğraf varyasyonu uygular: döndürme, aydınlatma değişimi, gürültü.
    Her varyasyon farklı çekim koşullarını simüle eder.
    """
    y, x = goruntu.shape[:2]

    # Hafif döndürme (±12 derece)
    aci = (varyasyon - 2) * 6.0
    M = cv2.getRotationMatrix2D((x/2, y/2), aci, 1.0)
    goruntu = cv2.warpAffine(goruntu, M, (x, y), borderMode=cv2.BORDER_REFLECT)

    # Aydınlatma değişimi (±30%)
    faktor = aydınlatma_guc + (varyasyon * 0.15 - 0.15)
    goruntu = np.clip(goruntu.astype(np.float32) * faktor, 0, 255).astype(np.uint8)

    # Gaussian gürültü ekle
    gurultu_std = 8 + varyasyon * 3
    gurultu = np.random.normal(0, gurultu_std, goruntu.shape).astype(np.float32)
    goruntu = np.clip(goruntu.astype(np.float32) + gurultu, 0, 255).astype(np.uint8)

    return goruntu


def uret():
    """10 kaplumbağa için 4'er sentetik fotoğraf üretir."""
    CIKTI_DIZINI.mkdir(parents=True, exist_ok=True)
    meta_veri = {}

    toplam_boyut = 0
    uretilen = 0

    print("=" * 55)
    print("  Sentetik Kaplumbağa Veri Seti Üreticisi")
    print("=" * 55)

    for idx, isim in enumerate(ISIMLER[:KAPLUMBAGA_SAYISI]):
        klasor = CIKTI_DIZINI / isim
        klasor.mkdir(exist_ok=True)

        # Bu kaplumbağa için sabit bireysel özellikler
        np.random.seed(idx * 17 + 3)
        temel_renk = kaplumbaga_rengi_uret(idx)
        leke_deseni = np.random.rand(21)   # 7 leke × 3 özellik
        aydinlatma = 0.85 + np.random.rand() * 0.3

        dosyalar = []
        for v in range(FOTOGRAF_SAYISI):
            # Arka plan (su/deniz tonu)
            goruntu = np.zeros((GORUNTU_BOYUTU, GORUNTU_BOYUTU, 3), dtype=np.uint8)
            goruntu[:] = (
                np.random.randint(60, 100),   # B — mavi ton
                np.random.randint(80, 120),   # G — yeşil ton
                np.random.randint(20, 50),    # R
            )

            # Kaplumbağa çiz
            goruntu = vucut_cizimleri_yap(goruntu, temel_renk, leke_deseni)

            # Fotoğraf varyasyonu uygula
            goruntu = varyasyon_uygula(goruntu, v, aydinlatma)

            # JPEG olarak kaydet
            dosya_adi = f"{isim}_{v+1}.jpg"
            dosya_yolu = klasor / dosya_adi
            cv2.imwrite(str(dosya_yolu), goruntu, [cv2.IMWRITE_JPEG_QUALITY, KALITE])

            boyut = dosya_yolu.stat().st_size
            toplam_boyut += boyut
            dosyalar.append(str(dosya_yolu.relative_to(Path(__file__).parent)))
            uretilen += 1

        meta_veri[isim] = {
            "indeks": idx,
            "dosyalar": dosyalar,
            "leke_deseni_ozeti": leke_deseni[:5].tolist(),
        }
        print(f"  ✓ {isim:15s} — {FOTOGRAF_SAYISI} fotoğraf üretildi")

    # Meta veri JSON dosyasına yaz
    meta_yol = CIKTI_DIZINI / "meta.json"
    with open(meta_yol, "w", encoding="utf-8") as f:
        json.dump(meta_veri, f, ensure_ascii=False, indent=2)

    print("=" * 55)
    print(f"  Toplam: {uretilen} fotoğraf, {toplam_boyut/1024:.1f} KB")
    print(f"  Meta veri: {meta_yol}")
    print("=" * 55)


if __name__ == "__main__":
    uret()
