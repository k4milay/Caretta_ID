"""
CarettaID Sistem Test Scripti

Bu script:
  1. 10 kaplumbağayı API'ye kaydeder
  2. Her kaplumbağanın 4 fotoğrafını yükler (1. fotoğraf referans)
  3. Kalan 3 fotoğraf ile /identify sorgusu yapar
  4. Doğruluk yüzdesi ve geçti/kaldı sonuçlarını raporlar

Kullanım:
  python data/test_system.py

Ön koşul: Backend çalışıyor olmalı (http://localhost:8000)
"""
import json
import sys
import time
from pathlib import Path

import httpx

# API temel URL'i
API_URL = "http://localhost:8000/api"

# Sentetik veri dizini
VERI_DIZINI = Path(__file__).parent / "sample_photos"


def api_iste(metot: str, yol: str, **kwargs) -> dict:
    """API isteği gönderir ve JSON yanıtı döndürür."""
    url = f"{API_URL}{yol}"
    try:
        yanit = httpx.request(metot, url, timeout=60.0, **kwargs)
        yanit.raise_for_status()
        return yanit.json()
    except httpx.HTTPStatusError as e:
        print(f"    [HATA] {metot} {yol}: {e.response.status_code} — {e.response.text[:200]}")
        return {}
    except Exception as e:
        print(f"    [HATA] {metot} {yol}: {e}")
        return {}


def kaplumbagalari_kaydet(meta: dict) -> dict[str, str]:
    """
    Her kaplumbağayı API'ye kaydeder ve ID'lerini döndürür.
    İlk fotoğraf referans gömme vektörü için yüklenir.

    Döndürür: {kaplumbağa_adı: uuid}
    """
    print("\n── Kaplumbağalar Kaydediliyor ──────────────────────")
    id_haritasi = {}

    for isim, bilgi in meta.items():
        # Profil oluştur
        yanit = api_iste("POST", "/turtles", json={"name": isim, "notes": "Sentetik test verisi"})
        if not yanit:
            print(f"  ✗ {isim} — profil oluşturulamadı")
            continue

        turtle_id = yanit["id"]
        id_haritasi[isim] = turtle_id

        # İlk fotoğrafı referans olarak yükle
        ref_dosya = Path(__file__).parent / bilgi["dosyalar"][0]
        if ref_dosya.exists():
            with open(ref_dosya, "rb") as f:
                fotograf_yanit = api_iste(
                    "POST", f"/turtles/{turtle_id}/photos",
                    files={"file": (ref_dosya.name, f, "image/jpeg")},
                    params={"region": "body"},
                )
            if fotograf_yanit:
                print(f"  ✓ {isim:15s} kaydedildi (id={turtle_id[:8]}…)")
            else:
                print(f"  ⚠ {isim:15s} kaydedildi ama fotoğraf yüklenemedi")
        else:
            print(f"  ✗ {isim} — referans fotoğraf bulunamadı: {ref_dosya}")

        # API'yi yormamak için kısa bekleme
        time.sleep(0.2)

    return id_haritasi


def tanimlama_testi_calistir(meta: dict, id_haritasi: dict[str, str]) -> list[dict]:
    """
    Her kaplumbağanın 2-4. fotoğraflarıyla /identify çağrısı yapar.

    Döndürür: test sonuçları listesi
    """
    print("\n── Tanımlama Testleri ──────────────────────────────")
    sonuclar = []

    for isim, bilgi in meta.items():
        if isim not in id_haritasi:
            continue

        dogru_id = id_haritasi[isim]

        # 2. fotoğraftan itibaren test (1. fotoğraf referans olarak yüklendi)
        test_fotograflari = bilgi["dosyalar"][1:]
        dogru_sayisi = 0

        for fotograf_yolu in test_fotograflari:
            dosya = Path(__file__).parent / fotograf_yolu
            if not dosya.exists():
                continue

            with open(dosya, "rb") as f:
                yanit = api_iste(
                    "POST", "/identify",
                    files={"file": (dosya.name, f, "image/jpeg")},
                    params={"region": "body", "top_k": 3},
                )

            if not yanit or not yanit.get("accepted"):
                sonuclar.append({
                    "kaplumbaga": isim,
                    "dosya": dosya.name,
                    "gecti": False,
                    "sebep": "eşleşme bulunamadı",
                })
                continue

            # En iyi eşleşmenin doğru kaplumbağa olup olmadığını kontrol et
            en_iyi = yanit["matches"][0]
            gecti = str(en_iyi["turtle_id"]) == dogru_id

            if gecti:
                dogru_sayisi += 1

            sonuclar.append({
                "kaplumbaga": isim,
                "dosya": dosya.name,
                "gecti": gecti,
                "benzerlik": en_iyi["similarity_score"],
                "tahmin": en_iyi["name"],
                "gercek": isim,
            })

            durum = "✓" if gecti else "✗"
            print(f"  {durum} {isim:15s} / {dosya.name:20s} → "
                  f"{'%' + str(round(en_iyi['similarity_score']*100))} benzerlik "
                  f"(tahmin: {en_iyi['name']})")

        time.sleep(0.1)

    return sonuclar


def rapor_yazdir(sonuclar: list[dict]) -> None:
    """Test sonuçlarını özetler ve doğruluk yüzdesini hesaplar."""
    print("\n" + "=" * 55)
    print("  TEST RAPORU")
    print("=" * 55)

    if not sonuclar:
        print("  Test sonucu yok.")
        return

    toplam = len(sonuclar)
    gecen = sum(1 for s in sonuclar if s["gecti"])
    kalan = toplam - gecen
    dogruluk = gecen / toplam * 100 if toplam > 0 else 0

    print(f"\n  Toplam test   : {toplam}")
    print(f"  Geçti         : {gecen}  ✓")
    print(f"  Kaldı         : {kalan}  ✗")
    print(f"  Doğruluk oranı: %{dogruluk:.1f}")

    if kalan > 0:
        print("\n  Başarısız testler:")
        for s in sonuclar:
            if not s["gecti"]:
                sebep = s.get("sebep", f"tahmin={s.get('tahmin','?')}")
                print(f"    ✗ {s['kaplumbaga']:15s} / {s['dosya']:20s} — {sebep}")

    print("\n" + "=" * 55)

    # Sonucu dosyaya yaz
    sonuc_dosya = Path(__file__).parent / "test_sonuclari.json"
    with open(sonuc_dosya, "w", encoding="utf-8") as f:
        json.dump({
            "toplam": toplam,
            "gecen": gecen,
            "kalan": kalan,
            "dogruluk_yuzde": round(dogruluk, 2),
            "detaylar": sonuclar,
        }, f, ensure_ascii=False, indent=2)
    print(f"  Detaylı sonuçlar: {sonuc_dosya}")


def main():
    print("\n" + "=" * 55)
    print("  CarettaID Sistem Test Scripti")
    print("=" * 55)

    # Sentetik veri kontrolü
    meta_yol = VERI_DIZINI / "meta.json"
    if not meta_yol.exists():
        print(f"\n[HATA] Meta veri bulunamadı: {meta_yol}")
        print("Önce veri üreticiyi çalıştırın:")
        print("  python data/generate_synthetic_data.py")
        sys.exit(1)

    with open(meta_yol, encoding="utf-8") as f:
        meta = json.load(f)

    # API erişilebilirlik kontrolü
    try:
        httpx.get(f"{API_URL.replace('/api','')}/api/health", timeout=5)
    except Exception:
        print(f"\n[HATA] API'ye erişilemiyor: {API_URL}")
        print("Backend çalışıyor mu? docker compose up --build")
        sys.exit(1)

    # Testleri çalıştır
    id_haritasi = kaplumbagalari_kaydet(meta)
    sonuclar = tanimlama_testi_calistir(meta, id_haritasi)
    rapor_yazdir(sonuclar)


if __name__ == "__main__":
    main()
