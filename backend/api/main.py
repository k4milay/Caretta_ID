from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.logging import configure_logging, get_logger
from api.routes import health, identify, photos, sightings, turtles

configure_logging()
log = get_logger("api")

_DESCRIPTION = """
## CarettaID — Yapay Zeka Destekli Caretta Tanıma Sistemi

Her caretta kaplumbağasının baş/yüz leke deseni parmak izi gibi benzersizdir.
Bu API, yüklenen fotoğrafları kayıtlı kaplumbağalarla karşılaştırır ve
**kosinüs benzerliği** tabanlı sıralı eşleşmeler döndürür.

### Kimlik Tespiti Boru Hattı

1. **Ön İşleme** — Görüntü doğrulama, 512×512 CLAHE normalizasyon, baş bölgesi segmentasyonu (GrabCut + adaptif eşik)
2. **Öznitelik Çıkarma** — EfficientNet-B0 omurgası → `Linear(1280→512)` + L2-norm → 512 boyutlu birim vektör
3. **Benzerlik Araması** — pgvector HNSW indeksinde kosinüs araması, güven bantlama (Yüksek ≥ 0.85 / Orta ≥ 0.70 / Düşük ≥ 0.60)

### Modüler Segmentasyon

Sistem **head** (baş) bölgesi ile çalışır. Karapaks (sırt kabuğu) segmentasyonu
strateji katmanı üzerinden eklenebilir — mevcut kod değişikliği gerekmez.
"""

_TAGS = [
    {"name": "identification", "description": "Fotoğraf yükle ve kimlik eşleşmelerini al."},
    {"name": "turtles",        "description": "Kaplumbağa profili CRUD işlemleri."},
    {"name": "photos",         "description": "Profillere fotoğraf ekle — otomatik olarak gömme vektörü oluşturulur."},
    {"name": "sightings",      "description": "GPS gözlem kaydı ve GeoJSON rota verisi."},
    {"name": "health",         "description": "Servis sağlık kontrolleri."},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("CarettaID API başlatılıyor")
    yield
    log.info("CarettaID API durduruluyor")


app = FastAPI(
    title="CarettaID API",
    version="0.1.0",
    description=_DESCRIPTION,
    openapi_tags=_TAGS,
    contact={"name": "k4milay", "email": "thekamilay@gmail.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(identify.router)
app.include_router(turtles.router)
app.include_router(photos.router)
app.include_router(sightings.router)

# Yüklenen fotoğrafları statik dosya olarak sun
_UPLOADS = Path("uploads")
_UPLOADS.mkdir(exist_ok=True)
app.mount("/api/static/uploads", StaticFiles(directory=str(_UPLOADS)), name="uploads")
