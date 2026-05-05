# CarettaID — Yapay Zeka Destekli Caretta Kaplumbağası Tanıma Sistemi

CarettaID, deniz kaplumbağalarının tam vücut fotoğraflarından bireysel kimliklerini tespit eden, çok ajanlı mimariye sahip bir yapay zeka sistemidir. Her kaplumbağanın karapaks deseni ve baş leke düzeni parmak izi gibi benzersizdir; sistem bu desenleri 4 aşamalı bir boru hattı ve 1024 boyutlu gömme vektörleriyle analiz eder.

---

## Kullanılan Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2 (async), Alembic |
| Veritabanı | PostgreSQL 16 + pgvector (HNSW indeksi) |
| ML/CV | EfficientNet-B0, OpenCV, PyTorch (CPU modu) |
| Frontend | React 18, TypeScript, Vite, Leaflet |
| Altyapı | Docker Compose |

---

## Kurulum Adımları

### Gereksinimler
- Docker Desktop (v4.0+)
- Node.js 18+ (frontend için)
- Git

### 1. Depoyu klonla

```bash
git clone https://github.com/k4milay/Caretta_ID.git
cd Caretta_ID
```

### 2. Backend ve veritabanını başlat

```bash
docker compose up --build
```

İlk çalıştırmada Docker imajları indirilir (~2 GB). Bu işlem 5–10 dakika sürebilir.

### 3. Veritabanı tablolarını oluştur

```bash
docker compose exec backend alembic upgrade head
```

### 4. Frontend geliştirme sunucusunu başlat

```bash
cd frontend
npm install
npm run dev
```

---

## Erişim Noktaları

| Adres | İçerik |
|-------|--------|
| `http://localhost:5173` | React arayüzü |
| `http://localhost:5173/identify` | Kaplumbağa sorgulama |
| `http://localhost:5173/turtles` | Kayıtlı kaplumbağa listesi |
| `http://localhost:8000/docs` | Swagger API dokümantasyonu |
| `http://localhost:8000/api/health` | Sağlık kontrolü |

---

## Kullanım Kılavuzu

### Kaplumbağa Sorgulama

1. Ana sayfada (`/identify`) fotoğraf yükleme alanına tıklayın veya fotoğrafı sürükleyin
2. **"Analiz Et"** butonuna basın
3. Sistem fotoğrafı işler ve sonuç döndürür:
   - **Kayıtlı bulunursa**: Kaplumbağanın adı ve benzerlik yüzdesi gösterilir
   - **Aday eşleşmeler**: %62–70 aralığında kalan olası eşleşmeler ayrıca listelenir
   - **Kayıtlı değilse**: "Yeni Kayıt Oluştur" seçeneği sunulur
   - **Kaplumbağa yoksa**: Fotoğrafta kaplumbağa tespit edilemediği bildirilir

### Yeni Kaplumbağa Kaydı

1. Navbar'dan **"+ Yeni Kayıt"** butonuna tıklayın
2. Ad ve notları doldurun, **"Devam Et"** deyin
3. Referans fotoğraf yükleyin (bu fotoğraf tanımlama için kullanılır)

### Profil Yönetimi

- **Galeri**: Yüklenen tüm fotoğraflar görüntülenir, büyütmek için tıklayın
- **Fotoğraf Ekle**: Yeni fotoğraf yükleyerek profilini güçlendirin
- **Gözlem Ekle**: GPS koordinatı ve konum adı girin
- **Hareket Rotası**: Leaflet haritasında görülen tüm konum noktaları

### Gömmeleri Yenileme (Admin)

Modeli değiştirdikten veya parametreleri güncelledikten sonra tüm fotoğrafların gömme vektörlerini yeniden hesaplamak için:

```bash
curl -X POST http://localhost:8000/api/admin/reembed
```

Bu endpoint her fotoğrafı diskten okuyarak tam 4-aşamalı pipeline ile işler; query ve stored embedding her zaman aynı uzayda kalır.

---

## Ajan Mimarisi

```
HTTP İsteği (/identify)
      │
      ▼
OrchestratorAgent
      │
      ├── Aşama 0: Kaplumbağa Tespit Kapısı
      │       └── EfficientNet-B0 ImageNet sınıflandırıcısı
      │           (Caretta caretta = class 33; olasılık < %0.5 → ret)
      │
      ├── Aşama 1: ImagePreprocessingAgent
      │       ├── Görüntü doğrulama (format, boyut)
      │       ├── CLAHE kontrast normalleştirme
      │       └── 3 bölge tespiti (baş / karapaks / vücut)
      │
      ├── Aşama 2: FeatureExtractionAgent
      │       ├── 1024-d birleşik gömme vektörü
      │       │     ├── Semantik 512-d (EfficientNet-B0, ×√0.60)
      │       │     └── Uzamsal renk 512-d (4×4 HSV ızgara histogramı, ×√0.40)
      │       ├── 3 bölge ağırlıklı birleştirme (baş×0.30 + karapaks×0.50 + vücut×0.20)
      │       └── L2-normalize son vektör
      │
      └── Aşama 3: SimilaritySearchAgent
              ├── pgvector HNSW kosinüs araması
              ├── Turtle bazında tekilleştirme
              └── Güven bantlama:
                    Yüksek  ≥ %76  (yeşil)
                    Orta    ≥ %73  (sarı)
                    Düşük   ≥ %70  (turuncu)
                    Aday    ≥ %62  (gri, kabul edilmez)
```

---

## Eşik Değerleri

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| `similarity_threshold` | 0.70 | Bu değerin üzerindeki eşleşmeler "kabul edildi" sayılır |
| `similarity_floor` | 0.62 | Bu değerin altı gösterilmez; üstü "aday" olarak listelenir |
| Kaplumbağa tespit eşiği | 0.005 | EfficientNet turtle sınıfları toplam olasılığı |

---

## Proje Yapısı

```
Caretta ID/
├── backend/
│   ├── agents/               # Çok ajanlı ML boru hattı
│   │   ├── orchestrator_agent.py
│   │   ├── preprocessing_agent.py
│   │   ├── feature_extraction_agent.py
│   │   └── similarity_search_agent.py
│   ├── api/routes/           # FastAPI rotaları
│   ├── core/                 # Veritabanı, config, bağımlılıklar
│   ├── migrations/           # Alembic migrasyonları
│   ├── models/               # SQLAlchemy ORM + Pydantic şemaları
│   ├── repositories/         # Veritabanı erişim katmanı
│   └── services/             # embedding_model.py (EfficientNet)
├── frontend/
│   └── src/
│       ├── pages/            # IdentifyPage, TurtlePage, vb.
│       ├── components/       # Navbar, DropZone, RouteMap
│       └── services/api.ts   # Typed fetch wrappers
├── data/
│   └── sample_photos/        # Örnek fotoğraf klasörü
└── docker-compose.yml
```
