# CarettaID — Yapay Zeka Destekli Caretta Kaplumbağası Tanıma Sistemi

CarettaID, deniz kaplumbağalarının tam vücut fotoğraflarından bireysel kimliklerini tespit eden, çok ajanlı mimariye sahip bir yapay zeka sistemidir. Her kaplumbağanın karapaks deseni ve baş leke düzeni parmak izi gibi benzersizdir; sistem bu desenleri EfficientNet-B0 omurgası ve pgvector veritabanı kullanarak analiz eder.

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

1. Ana sayfada (`/`) fotoğraf yükleme alanına tıklayın veya fotoğrafı sürükleyin
2. **"Analiz Et"** butonuna basın
3. Sistem fotoğrafı işler ve sonuç döndürür:
   - **Kayıtlı bulunursa**: Kaplumbağanın adı ve benzerlik yüzdesi gösterilir, profile yönlendirilirsiniz
   - **Kayıtlı değilse**: "Yeni Kayıt Oluştur" seçeneği sunulur

### Yeni Kaplumbağa Kaydı

1. Navbar'dan **"+ Yeni Kayıt"** butonuna tıklayın
2. Ad ve notları doldurun, **"Devam Et"** deyin
3. Referans fotoğraf yükleyin (bu fotoğraf tanımlama için kullanılır)

### Profil Yönetimi

- **Galeri**: Yüklenen tüm fotoğraflar görüntülenir, büyütmek için tıklayın
- **Fotoğraf Ekle**: Yeni fotoğraf yükleyerek gömme vektörünü güncelleyin
- **Gözlem Ekle**: GPS koordinatı ve konum adı girin
- **Hareket Rotası**: Leaflet haritasında görülen tüm konum noktaları

---

## Sentetik Test Verisi

Sistemi test etmek için sentetik veri üreticisini çalıştırın:

```bash
# Sentetik veri oluştur (10 kaplumbağa × 4 fotoğraf)
python data/generate_synthetic_data.py

# Sistem doğruluk testini çalıştır
python data/test_system.py
```

---

## Ajan Mimarisi

```
HTTP İsteği (/identify)
      │
      ▼
OrchestratorAgent
      │
      ├── 1. ImagePreprocessingAgent
      │       ├── Görüntü doğrulama (format, boyut)
      │       ├── CLAHE kontrast normalleştirme
      │       └── 3 bölge tespiti (baş / karapaks / vücut)
      │
      ├── 2. FeatureExtractionAgent
      │       ├── Baş bölgesi gömme × 0.30
      │       ├── Karapaks gömme × 0.50
      │       ├── Vücut gömme × 0.20
      │       └── L2-normalize birleşik vektör (512-d)
      │
      └── 3. SimilaritySearchAgent
              ├── pgvector HNSW kosinüs araması
              ├── Turtle bazında tekilleştirme
              └── Güven bantlama (Yüksek ≥ %92 / Orta ≥ %85 / Düşük ≥ %78)
```

---

## Ekran Görüntüleri

> _Ekran görüntüleri eklenecek_

---




