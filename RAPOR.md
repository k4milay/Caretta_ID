# CarettaID — Teknik Tasarım ve Uygulama Raporu

**Proje:** CarettaID — Yapay Zeka Destekli Caretta Kaplumbağası Tanıma Sistemi  
**Geliştirici:** Kamil Ay (`k4milay`)  
**Tarih:** Mayıs 2026  
**Depo:** `github.com/k4milay/Caretta_ID`

---

## 1. Proje Özeti

Caretta caretta (adi deniz kaplumbağası) Akdeniz'de nesli tehlike altındadır. Bireysel takip, popülasyon dinamiklerini anlamak için kritiktir; ancak geleneksel flipper etiketleme hem hayvanı hem araştırmacıyı riske atar.

**CarettaID**, invazif olmayan fotoğraf tabanlı bir tanımlama sistemidir. Her kaplumbağanın karapaks (kabuk) deseni ve baş leke örüntüsü parmak izi gibi benzersizdir. Sisteme yüklenen fotoğraf, kayıtlı tüm bireylerle karşılaştırılır; eşleşme bulunursa profil gösterilir, bulunmazsa yeni kayıt oluşturulur.

| Katman | Teknoloji | Sürüm |
|--------|-----------|-------|
| **Backend** | Python, FastAPI, SQLAlchemy 2 (async), Alembic | Python 3.11 |
| **Veritabanı** | PostgreSQL + pgvector (HNSW indeksi) | PG 16 |
| **ML/CV** | EfficientNet-B0, OpenCV, PyTorch (CPU modu) | torch 2.4.1 |
| **Frontend** | React, TypeScript, Vite, Leaflet.js | React 18 |
| **Altyapı** | Docker Compose, StaticFiles | Docker 4.x |

| Metrik | Değer |
|--------|-------|
| Toplam Python dosyası | ~35 |
| Backend ajan sayısı | 6 |
| API uç noktası | 12 |
| Birim + entegrasyon testi | 14 test dosyası |
| Toplam test kapsamı | **%92** |
| Gömme boyutu | 512-d (L2-normalize) |
| Benzerlik eşiği (varsayılan) | 0.78 (kosinüs) |

---

## 2. Mimari Genel Bakış

### 2.1 Katmanlı Mimari

```
┌─────────────────────────────────────────────────────────┐
│                    SUNUM KATMANI                        │
│   React 18 + TypeScript + Vite   │   Leaflet.js Harita │
│   DropZone  IdentifyPage  TurtleProfilePage  Navbar     │
└─────────────────────┬───────────────────────────────────┘
                      │  HTTP / JSON  (port 5173 → 8000)
┌─────────────────────▼───────────────────────────────────┐
│                    API KATMANI                          │
│   FastAPI   /api/identify   /api/turtles   /api/health  │
│   Pydantic şema doğrulama   StaticFiles /api/static/    │
└─────────────────────┬───────────────────────────────────┘
                      │  dependency injection
┌─────────────────────▼───────────────────────────────────┐
│                    AJAN KATMANI                         │
│  OrchestratorAgent ──► PreprocessingAgent               │
│                    ──► FeatureExtractionAgent           │
│                    ──► SimilaritySearchAgent            │
│  ProfileManagementAgent    SightingTrackerAgent         │
└─────────────────────┬───────────────────────────────────┘
                      │  Repository pattern
┌─────────────────────▼───────────────────────────────────┐
│                 VERİ ERİŞİM KATMANI                     │
│  TurtleRepository   PhotoRepository   SightingRepository│
│  SQLAlchemy 2 async   pgvector HNSW   asyncpg           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 ALTYAPI KATMANI                         │
│     PostgreSQL 16 + pgvector        Docker Compose      │
│     Alembic migration               uploads/ volume     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Klasör Yapısı

```
Caretta_ID/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py              ← BaseAgent[TIn, TOut] + AgentResult
│   │   ├── preprocessing_agent.py     ← Görüntü doğrulama + 3 bölge kırpma
│   │   ├── feature_extraction_agent.py← EfficientNet-B0 ağırlıklı gömme
│   │   ├── similarity_search_agent.py ← pgvector HNSW + güven bantlama
│   │   ├── orchestrator_agent.py      ← Boru hattı koordinatörü
│   │   ├── profile_management_agent.py← Kaplumbağa CRUD + fotoğraf yükleme
│   │   └── sighting_tracker_agent.py  ← GPS gözlem + GeoJSON rota
│   ├── api/
│   │   ├── main.py                    ← FastAPI app + StaticFiles
│   │   └── routes/
│   │       ├── photos.py              ← /turtles/{id}/photos
│   │       ├── turtles.py             ← /turtles CRUD
│   │       ├── identify.py            ← /identify
│   │       └── sightings.py           ← /sightings
│   ├── core/
│   │   ├── config.py                  ← Pydantic Settings
│   │   ├── container.py               ← DI container (lru_cache singletons)
│   │   └── logging.py                 ← Yapılandırılmış logger
│   ├── models/
│   │   ├── db.py                      ← SQLAlchemy ORM (Turtle, Photo, Sighting)
│   │   └── schemas.py                 ← Pydantic I/O şemaları
│   ├── repositories/
│   │   ├── turtle_repository.py
│   │   ├── photo_repository.py        ← upsert_embedding, search_by_embedding
│   │   └── sighting_repository.py
│   ├── services/
│   │   ├── embedding_model.py         ← EfficientNet-B0 + 512-d projeksiyon
│   │   └── segmentation/
│   │       ├── base.py                ← SegmentationStrategy ABC
│   │       ├── factory.py             ← strateji seçici
│   │       └── grabcut.py             ← GrabCut tabanlı segmentasyon
│   └── tests/                         ← 14 test dosyası, %92 kapsam
├── frontend/
│   └── src/
│       ├── pages/                     ← IdentifyPage, TurtleProfilePage, …
│       ├── components/                ← Navbar, DropZone
│       └── services/api.ts            ← tüm API çağrıları
├── data/
│   ├── generate_synthetic_data.py     ← 10 kaplumbağa × 4 fotoğraf üretici
│   └── test_system.py                 ← uçtan-uca doğruluk testi
├── ml/training/train_arcface.py       ← Gelecek: metrik öğrenme ince ayarı
├── docker-compose.yml
├── README.md
└── RAPOR.md
```

---

## 3. SOLID Prensipleri

### 3.1 Tek Sorumluluk İlkesi (SRP)

Her ajan yalnızca tek bir sorumluluğa sahiptir. Boru hattının herhangi bir adımını değiştirmek diğer ajanları etkilemez.

```
Ajan                      Sorumluluk
──────────────────────    ─────────────────────────────────────────────
ImagePreprocessingAgent   Bayt doğrulama, CLAHE normalleştirme, 3 bölge kırp
FeatureExtractionAgent    EfficientNet-B0 ile ağırlıklı 512-d gömme üret
SimilaritySearchAgent     pgvector HNSW arama + güven bantlama
OrchestratorAgent         Üç aşamayı sıraya koy, hataları yüzeye çıkar
ProfileManagementAgent    Kaplumbağa profili ve fotoğraf CRUD
SightingTrackerAgent      GPS gözlem kaydı + GeoJSON rota üretimi
```

**SRP ihlali olsaydı** — OrchestratorAgent hem görüntüyü işlese hem araştırma yapsa, CLAHE parametresini değiştirmek benzerlik eşiğini etkileyen bir dosyayı da değiştirirdi.

```python
# backend/agents/preprocessing_agent.py
class ImagePreprocessingAgent(BaseAgent[PreprocessingInput, PreprocessingOutput]):
    """Tek sorumluluk: ham baytı, özellik çıkarımına hazır numpy dizisine çevirmek."""

    async def _execute(self, payload: PreprocessingInput) -> PreprocessingOutput:
        self._baytlari_dogrula(payload.image_bytes)   # Doğrulama
        goruntu = self._coz(payload.image_bytes)       # Çözme
        self._boyutu_dogrula(goruntu)
        normallestirilmis = self._normallesтir(goruntu)  # CLAHE normalleştirme
        bas, karapaks, vucut = self._bolgeleri_kirp(normallestirilmis)
        seg = get_strategy(payload.region).segment(normallestirilmis)
        return PreprocessingOutput(
            normalised=normallestirilmis, segmentation=seg,
            original_size=(goruntu.shape[1], goruntu.shape[0]),
            region_head=bas, region_carapace=karapaks, region_body=vucut,
        )
```

### 3.2 Açık/Kapalı İlkesi (OCP)

`SegmentationStrategy` soyut sınıfı sayesinde yeni segmentasyon algoritmaları mevcut kodu değiştirmeden eklenebilir.

```python
# backend/services/segmentation/base.py
class SegmentationStrategy(ABC):
    region_name: str = "unknown"

    @abstractmethod
    def segment(self, image: np.ndarray) -> SegmentationResult:
        """Normalleştirilmiş görüntüden ROI ve ikili leke maskesi çıkar."""
```

Yeni bir YOLO tabanlı baş tespiti eklemek için:

```python
# backend/services/segmentation/yolo_head.py  ← YENİ DOSYA
class YOLOHeadStrategy(SegmentationStrategy):
    region_name = "head"

    def segment(self, image: np.ndarray) -> SegmentationResult:
        # YOLO ile baş tespiti — mevcut hiçbir dosyaya dokunulmaz
        ...
```

Benzer şekilde `SimilaritySearchAgent` içindeki `SimilarityStrategy` arayüzü de OCP'yi uygular:

```python
# backend/agents/similarity_search_agent.py
class SimilarityStrategy(ABC):
    @abstractmethod
    def score(self, query: np.ndarray, candidate: np.ndarray) -> float: ...

class CosineStrategy(SimilarityStrategy):      # Varsayılan — L2-normalize vektörler için
    def score(self, q, c): return float(np.dot(q, c))

class EuclideanStrategy(SimilarityStrategy):   # Alternatif — OCP ile eklendi
    def score(self, q, c): return float(np.exp(-np.linalg.norm(q - c)))
```

### 3.3 Liskov Yerine Geçme İlkesi (LSP)

Tüm beton ajanlar `BaseAgent[TIn, TOut]` türünü genişletir. Orkestratör, hangi somut implementasyonun kullanıldığını bilmeksizin `run()` metodunu çağırır.

```python
# backend/agents/base_agent.py
class BaseAgent(ABC, Generic[TIn, TOut]):
    async def run(self, payload: TIn) -> AgentResult[TOut]:
        start = time.perf_counter()
        self.log.info("start")
        try:
            value = await self._execute(payload)      # ← her alt sınıf buraya girer
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            return AgentResult(ok=False, value=None, error=str(exc), duration_ms=duration)
        duration = (time.perf_counter() - start) * 1000
        return AgentResult(ok=True, value=value, error=None, duration_ms=duration)

    @abstractmethod
    async def _execute(self, payload: TIn) -> TOut: ...
```

Orkestratör'ün `_basarili_mi()` kontrolü her ajan için aynı arayüzle çalışır — LSP gereği beton sınıf fark etmez:

```python
# backend/agents/orchestrator_agent.py
@staticmethod
def _basarili_mi(sonuc: AgentResult, asama: str) -> None:
    if not sonuc.ok:
        raise RuntimeError(f"{asama} aşaması başarısız: {sonuc.error}")
```

### 3.4 Arayüz Ayrımı İlkesi (ISP)

Her repository yalnızca ilgili varlık için gereken metodları barındırır. Fotograf ajanı hiçbir zaman kaplumbağa CRUD metodlarına erişemez.

```python
# PhotoRepository — sadece fotoğraf işlemleri
class PhotoRepository:
    async def create(self, turtle_id, file_path) -> Photo: ...
    async def upsert_embedding(self, photo_id, embedding) -> None: ...
    async def search_by_embedding(self, embedding, top_k, ...) -> list[EmbeddingMatch]: ...
    async def list_by_turtle(self, turtle_id) -> list[Photo]: ...
    async def get_by_id(self, photo_id) -> Photo | None: ...

# TurtleRepository — sadece kaplumbağa işlemleri
class TurtleRepository:
    async def create(self, name, notes) -> Turtle: ...
    async def get_by_id(self, turtle_id) -> Turtle | None: ...
    async def list_all(self) -> list[Turtle]: ...
    async def get_by_ids(self, ids) -> list[Turtle]: ...
```

### 3.5 Bağımlılık Ters Çevirme İlkesi (DIP)

`FeatureExtractionAgent` gerçek PyTorch fonksiyonuna değil, soyut bir `EmbedFn` callable'a bağımlıdır. Test ortamında sahte fonksiyon enjekte edilir; hiçbir zaman GPU başlatılmaz.

```python
# backend/agents/feature_extraction_agent.py
EmbedFn = Callable[[np.ndarray], np.ndarray]

class FeatureExtractionAgent(BaseAgent[FeatureInput, FeatureOutput]):
    def __init__(self, embed_fn: EmbedFn = embed_image) -> None:
        super().__init__()
        self._embed = embed_fn  # Test → deterministik sahte; Prod → EfficientNet-B0
```

Testte enjeksiyon:

```python
# backend/tests/test_feature_extraction_agent.py
def fake_embed(img: np.ndarray) -> np.ndarray:
    vec = np.ones(512, dtype=np.float32)
    return vec / np.linalg.norm(vec)   # L2-normalize sahte vektör

agent = FeatureExtractionAgent(embed_fn=fake_embed)
```

---

## 4. Clean Code Prensipleri

### 4.1 Anlamlı İsimlendirme

Fonksiyon ve değişken adları, ne yaptığını açıkça ortaya koyar. Yorum gerekmez.

```python
# Kötü
def proc(b, r):
    arr = np.frombuffer(b, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

# Doğru — backend/agents/preprocessing_agent.py
def _coz(self, veri: bytes) -> np.ndarray:
    dizi = np.frombuffer(veri, dtype=np.uint8)
    goruntu = cv2.imdecode(dizi, cv2.IMREAD_COLOR)
    if goruntu is None:
        raise ValueError("Görüntü çözümlemesi başarısız — dosya bozuk olabilir.")
    return goruntu
```

### 4.2 Küçük ve Odaklanmış Fonksiyonlar

Her yardımcı metod tek bir işi yapar, parametresi yok veya çok az vardır.

```python
# backend/agents/preprocessing_agent.py
def _baytlari_dogrula(self, veri: bytes) -> None: ...   # 6 satır
def _coz(self, veri: bytes) -> np.ndarray: ...          # 5 satır
def _boyutu_dogrula(self, goruntu: np.ndarray) -> None: # 4 satır
def _normallesтir(self, goruntu: np.ndarray) -> np.ndarray: ...  # 10 satır
def _bolgeleri_kirp(...) -> tuple[...]: ...             # 14 satır
```

### 4.3 Sabitler, Sihirli Sayılar Değil

Tüm kritik sayısal değerler modül düzeyinde adlandırılmış sabitler olarak tanımlanır.

```python
# backend/agents/preprocessing_agent.py
_MIN_KENAR_PX = 64                # Minimum kabul edilebilir görüntü boyutu
_MAX_BAYT = 20 * 1024 * 1024      # 20 MB dosya boyutu sınırı
_HEDEF_BOYUT = (224, 224)         # Model girişi için standart boyut

# backend/agents/feature_extraction_agent.py
_AGIRLIK_BAS = 0.30       # Baş/yüz lekeleri ağırlığı
_AGIRLIK_KARAPAKS = 0.50  # Karapaks/kabuk deseni ağırlığı
_AGIRLIK_VUCUT = 0.20     # Genel vücut şekli ağırlığı

# backend/agents/similarity_search_agent.py
_GUVEN_BANTLARI = [
    (0.92, "high"),    # Yüksek güven: %92 ve üzeri
    (0.85, "medium"),  # Orta güven:   %85 – %92
    (0.78, "low"),     # Düşük güven:  %78 – %85
]
```

### 4.4 Tip Güvenliği

Her ajan kendi `Input` ve `Output` dataclass'larını tanımlar. Python'un `Generic[TIn, TOut]` sistemi derleme zamanı tip kontrolü sağlar.

```python
@dataclass
class PreprocessingInput:
    image_bytes: bytes
    region: str = "body"

@dataclass
class PreprocessingOutput:
    normalised: np.ndarray
    segmentation: SegmentationResult
    original_size: tuple[int, int]
    region_head: np.ndarray       # %30 ağırlık
    region_carapace: np.ndarray   # %50 ağırlık
    region_body: np.ndarray       # %20 ağırlık
```

### 4.5 Erken Dönüş (Guard Clause)

İç içe geçmiş koşullar yerine erken fırlat/dön yaklaşımı kullanılır.

```python
# Kötü
async def _execute(self, payload):
    if payload.image_bytes:
        if len(payload.image_bytes) > 0:
            # asıl mantık
            ...

# Doğru — backend/agents/preprocessing_agent.py
def _baytlari_dogrula(self, veri: bytes) -> None:
    if len(veri) == 0:
        raise ValueError("Boş görüntü verisi.")
    if len(veri) > _MAX_BAYT:
        raise ValueError(f"Görüntü {_MAX_BAYT // (1024*1024)} MB sınırını aşıyor.")
    baslik = veri[:4]
    if not any(baslik.startswith(sihir) for sihir in _GECERLI_SIHIRLI):
        raise ValueError("Desteklenmeyen format. Kabul edilen: JPEG, PNG, BMP, WebP.")
```

---

## 5. Çoklu Ajan Mimarisi

### 5.1 Ajan Bağımlılık Grafiği

```
HTTP /identify
     │
     ▼
OrchestratorAgent
     │
     ├── 1 ──► ImagePreprocessingAgent
     │               └── SegmentationStrategy (GrabCut / YOLO*)
     │
     ├── 2 ──► FeatureExtractionAgent
     │               └── embed_fn (EfficientNet-B0 / sahte*)
     │
     └── 3 ──► SimilaritySearchAgent
                     ├── PhotoRepository  ──► PostgreSQL pgvector
                     ├── TurtleRepository ──► PostgreSQL
                     └── SimilarityStrategy (Cosine / Euclidean*)

HTTP /turtles/{id}/photos
     │
     ▼
ProfileManagementAgent
     ├── PhotoRepository (create, upsert_embedding)
     └── FeatureExtractionAgent

HTTP /sightings
     │
     ▼
SightingTrackerAgent
     └── SightingRepository (create, GeoJSON)

* = OCP ile kolayca değiştirilebilir
```

### 5.2 Ajan Detayları

#### ImagePreprocessingAgent

| Alan | Değer |
|------|-------|
| Dosya | `backend/agents/preprocessing_agent.py` |
| Giriş | `PreprocessingInput(image_bytes, region)` |
| Çıkış | `PreprocessingOutput(normalised, segmentation, original_size, region_head, region_carapace, region_body)` |
| Strateji | `SegmentationStrategy` inject edilir |
| CLAHE | `clipLimit=2.0, tileGridSize=(8,8)` LAB L kanalı |
| Bölgeler | Baş: üst %30 · Karapaks: %20–%85 · Vücut: tam görüntü |

#### FeatureExtractionAgent

| Alan | Değer |
|------|-------|
| Dosya | `backend/agents/feature_extraction_agent.py` |
| Giriş | `FeatureInput(image, mask, region_head, region_carapace, region_body)` |
| Çıkış | `FeatureOutput(embedding[512], dim, model_version)` |
| Model | EfficientNet-B0 (ImageNet ağırlıkları) + 512-d projeksiyon |
| Gömme formülü | `v = 0.30·v_baş + 0.50·v_karapaks + 0.20·v_vücut` |
| Normalize | L2 (‖v‖₂ = 1.0 ± 0.1 doğrulanır) |

```python
# Ağırlıklı gömme hesabı
v_bas      = self._embed(payload.region_head).astype(np.float64)
v_karapaks = self._embed(payload.region_carapace).astype(np.float64)
v_vucut    = self._embed(payload.region_body).astype(np.float64)

birlesik = _AGIRLIK_BAS * v_bas + _AGIRLIK_KARAPAKS * v_karapaks + _AGIRLIK_VUCUT * v_vucut
norm = np.linalg.norm(birlesik)
return (birlesik / norm).astype(np.float32)
```

#### SimilaritySearchAgent

| Alan | Değer |
|------|-------|
| Dosya | `backend/agents/similarity_search_agent.py` |
| Giriş | `SimilarityInput(embedding, top_k, threshold, exclude_photo_id)` |
| Çıkış | `SimilarityOutput(matches, threshold, accepted)` |
| İndeks | pgvector HNSW kosinüs (`<=>` operatörü) |
| Tekilleştirme | Kaplumbağa başına en yüksek skor tutulur |
| Güven bantları | Yüksek ≥ %92 · Orta ≥ %85 · Düşük ≥ %78 |

```python
# pgvector HNSW sorgusu — backend/repositories/photo_repository.py
raw = await session.execute(text(
    f"SELECT id, turtle_id, embedding <=> {vec_literal}::vector AS dist "
    f"FROM photos WHERE embedding IS NOT NULL {exclude_clause} "
    f"ORDER BY dist LIMIT :k"
), {"k": top_k})
```

#### OrchestratorAgent

| Alan | Değer |
|------|-------|
| Dosya | `backend/agents/orchestrator_agent.py` |
| Giriş | `IdentifyInput(image_bytes, region, top_k, threshold, exclude_photo_id)` |
| Çıkış | `IdentificationResponse(matches, threshold, accepted)` |
| Hata politikası | Her aşamada `AgentResult.ok` kontrolü; başarısız aşama RuntimeError fırlatır |

#### ProfileManagementAgent

| Alan | Değer |
|------|-------|
| Giriş | `ProfileInput(turtle_id, image_bytes, region)` |
| Çıkış | `ProfileOutput(photo_id, embedding_dim, message)` |
| Yaptıkları | Fotoğraf kaydı + gömme vektörü hesapla + DB'ye yaz |

#### SightingTrackerAgent

| Alan | Değer |
|------|-------|
| Giriş | `SightingInput(turtle_id, latitude, longitude, location_name, observed_at)` |
| Çıkış | `SightingOutput(sighting_id, geojson_route)` |
| GeoJSON | `FeatureCollection` ile bireysel hareket rotası |

---

## 6. AgentResult Mekanizması

Her ajan, `BaseAgent.run()` üzerinden çağrılır. Bu metod:
1. Süreyi ölçer (`perf_counter`)
2. Yapılandırılmış loglama yapar (`agent.<isim>` logger)
3. İstisnaları yakalar ve `AgentResult(ok=False, error=...)` olarak sarar

**Akış:**

```
ajan.run(payload)
    │
    ├── perf_counter() ── start
    ├── log.info("start")
    ├── _execute(payload) ────────────────────────────► Başarı
    │       │                                               │
    │       └── Exception ─────────────────────────► Hata  │
    │                                                  │    │
    ▼                                                  ▼    ▼
AgentResult(ok=False, value=None,        AgentResult(ok=True, value=output,
            error=str(exc),                          error=None,
            duration_ms=…)                           duration_ms=…)
```

**Frozen dataclass** olduğundan sonuç değiştirilemez ve güvenli şekilde iletilir:

```python
@dataclass(frozen=True)
class AgentResult(Generic[TOut]):
    ok: bool
    value: TOut | None
    error: str | None
    duration_ms: float
```

---

## 7. Port/Adapter (Bağlantı Noktası) Deseni

### 7.1 SegmentationStrategy — Görüntü Segmentasyon Portu

```
                ┌─────────────────────────┐
                │   SegmentationStrategy  │  ← Port (ABC)
                │   segment(image) →      │
                │   SegmentationResult    │
                └────────────┬────────────┘
                             │ implements
           ┌─────────────────┼──────────────────┐
           ▼                 ▼                  ▼
   GrabCutStrategy     YOLOHeadStrategy*   CustomStrategy*
   (mevcut adapter)    (gelecek adapter)   (3. parti adapter)

* OCP ile eklenir — mevcut kod değişmez
```

### 7.2 Repository — Veri Erişim Portu

```
                ┌─────────────────────────┐
                │    PhotoRepository      │  ← Port
                │    TurtleRepository     │
                │    SightingRepository   │
                └────────────┬────────────┘
                             │
                    AsyncSession (SQLAlchemy)
                             │
                    PostgreSQL 16 + pgvector
```

Backing store değiştirilmek istendiğinde (örn. Qdrant'a geçiş), yalnızca `PhotoRepository.search_by_embedding` değişir — hiçbir ajan kodu etkilenmez.

### 7.3 EmbedFn — Model Portu

```
FeatureExtractionAgent
        │
        └── embed_fn: EmbedFn
                │
                ├── embed_image()         ← Prod: EfficientNet-B0 / PyTorch
                ├── fake_embed()          ← Test: deterministik numpy
                └── arcface_embed()*      ← Gelecek: ince ayarlı model
```

---

## 8. Tanımlama İş Akışı

### 8.1 Kaplumbağa Sorgulama (`POST /api/identify`)

```
Kullanıcı fotoğraf yükler
         │
         ▼
   [FastAPI Route /identify]
         │ image_bytes + region + top_k
         ▼
   OrchestratorAgent.run(IdentifyInput)
         │
         ├─ Aşama 1 ──► ImagePreprocessingAgent
         │                   ├─ Bayt doğrulama (format, boyut)
         │                   ├─ CLAHE normalleştirme (224×224)
         │                   ├─ Baş bölgesi  → region_head   [0:67,  :]
         │                   ├─ Karapaks     → region_carapace[45:190,:]
         │                   └─ Vücut        → region_body   (tam)
         │                   AgentResult(ok=True, value=PreprocessingOutput)
         │
         ├─ Aşama 2 ──► FeatureExtractionAgent
         │                   ├─ embed(region_head)      → v_baş      [512-d]
         │                   ├─ embed(region_carapace)  → v_karapaks [512-d]
         │                   ├─ embed(region_body)      → v_vücut    [512-d]
         │                   ├─ birlesik = 0.30·v_baş + 0.50·v_karapaks + 0.20·v_vücut
         │                   └─ L2-normalize → embedding [512-d, ‖v‖=1.0]
         │                   AgentResult(ok=True, value=FeatureOutput)
         │
         └─ Aşama 3 ──► SimilaritySearchAgent
                             ├─ pgvector: embedding <=> kayıtlı_vektörler (HNSW)
                             ├─ Eşik filtrele (≥ 0.78)
                             ├─ Kaplumbağa başına tekilleştir
                             └─ Güven bantla: ≥0.92 high / ≥0.85 medium / ≥0.78 low
                             AgentResult(ok=True, value=SimilarityOutput)
         │
         ▼
   IdentificationResponse
         ├── accepted: true/false
         ├── matches: [{turtle_id, name, similarity_score, confidence}]
         └── threshold: 0.78

         │
         ├── accepted=true  → "Athena bulundu — %94 benzerlik (Yüksek güven)"
         └── accepted=false → "Yeni kaplumbağa — kayıt oluşturulsun mu?"
```

### 8.2 Yeni Kaplumbağa Kaydı (`POST /api/turtles` + `POST /api/turtles/{id}/photos`)

```
Kullanıcı "Yeni Kayıt" butonuna tıklar
         │
         ▼
   POST /api/turtles  { name: "Athena", notes: "..." }
         │
         ▼
   TurtleRepository.create() → Turtle(id=uuid, name="Athena")
         │
         ▼  HTTP 201 + turtle_id

   POST /api/turtles/{id}/photos (fotoğraf yükle)
         │
         ▼
   ProfileManagementAgent.run(ProfileInput)
         │
         ├─ PhotoRepository.create(turtle_id, file_path)  → Photo(id=uuid)
         │
         ├─ FeatureExtractionAgent.run(FeatureInput)
         │       └─ 3 bölge ağırlıklı gömme → embedding[512]
         │
         └─ PhotoRepository.upsert_embedding(photo_id, embedding)
                 └─ UPDATE photos SET embedding = '[...]'::vector WHERE id = ?
         │
         ▼
   ProfileOutput(photo_id, embedding_dim=512, message="Gömme başarıyla oluşturuldu")
```

---

## 9. Kritik Teknik Çözümler

### 9.1 pgvector Tip Uyuşmazlığı

asyncpg, Python listesini `vector` tipine dönüştüremiyordu:

```
DataError: invalid input for query argument $1: [...] (expected str, got list)
```

**Çözüm:** Vektörü SQL literal string olarak formatla:

```python
# Hatalı
await session.execute(text("UPDATE photos SET embedding = :vec WHERE id = :id"),
                      {"vec": embedding.tolist(), "id": str(photo_id)})  # ← tip hatası

# Doğru — backend/repositories/photo_repository.py
vec_literal = f"'[{','.join(str(x) for x in embedding.tolist())}]'"
await session.execute(
    text(f"UPDATE photos SET embedding = {vec_literal}::vector WHERE id = :id"),
    {"id": str(photo_id)},
)
```

### 9.2 Docker İmaj Boyutu

`torch==2.4.1` pip'ten kurulunca CUDA kütüphaneleri (~3 GB) de indiriliyordu.

**Çözüm:** CPU-only PyTorch'u ayrı index'ten önce kur:

```dockerfile
# backend/Dockerfile
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.4.1+cpu torchvision==0.19.1+cpu && \
    grep -v "^torch" requirements.txt | grep -v "^torchvision" > /tmp/req_notorch.txt && \
    pip install --no-cache-dir -r /tmp/req_notorch.txt
```

**Sonuç:** İmaj boyutu ~3 GB'tan ~1.2 GB'a düştü.

### 9.3 lru_cache Singleton ve Test İzolasyonu

`lru_cache` ile sarılmış ajan singletonları `dependency_overrides` ile geçersiz kılınamıyordu.

**Çözüm:** Orchestrator ve ProfileAgent fabrikalarının kendisini override ederek bağımlılıkları doğrudan enjekte etmek:

```python
# Test konfig
app.dependency_overrides[get_orchestrator] = lambda: OrchestratorAgent(
    preprocessing=ImagePreprocessingAgent(strategy=MockStrategy()),
    feature_extraction=FeatureExtractionAgent(embed_fn=fake_embed),
    similarity_search=SimilaritySearchAgent(mock_photo_repo, mock_turtle_repo),
)
```

---

## 10. Test Yapısı

| Test Dosyası | Tür | Test Sayısı | Kapsanan Alan |
|---|---|---|---|
| `test_base_agent.py` | Birim | 4 | AgentResult, hata sarma, süre ölçümü |
| `test_preprocessing_agent.py` | Birim | 8 | Bayt doğrulama, CLAHE, 3 bölge kırpma |
| `test_feature_extraction_agent.py` | Birim | 6 | Ağırlıklı gömme, L2-normalize, sahte embed |
| `test_similarity_search_agent.py` | Birim | 7 | Güven bantlama, tekilleştirme, eşik filtresi |
| `test_orchestrator_agent.py` | Birim | 5 | 3 aşama bağlantısı, hata yayılımı |
| `test_profile_management_agent.py` | Birim | 6 | CRUD, gömme güncelleme |
| `test_sighting_tracker_agent.py` | Birim | 4 | GPS kayıt, GeoJSON üretimi |
| `test_segmentation.py` | Birim | 5 | GrabCut strateji, SegmentationResult |
| `test_repositories.py` | Entegrasyon | 10 | pgvector arama, HNSW, turtle CRUD |
| `test_integration.py` | Uçtan-uca | 8 | Tam boru hattı, /identify akışı |
| `test_health.py` | API | 2 | /api/health 200 OK |
| `test_agent_branches.py` | Birim | 6 | Kenar durumlar, boş görüntü, sıfır vektör |
| `conftest.py` | Yardımcı | — | Test fixtures, mock repo'lar |

### Kapsam Raporu (Faz 6 sonrası)

| Modül | Kapsam |
|-------|--------|
| `repositories/turtle_repository` | %100 |
| `repositories/sighting_repository` | %100 |
| `repositories/photo_repository` | %100 |
| `agents/profile_management_agent` | %99 |
| `core/container` | %95 |
| `agents/preprocessing_agent` | %94 |
| `agents/feature_extraction_agent` | %93 |
| `agents/similarity_search_agent` | %91 |
| **Toplam** | **%92** |

---

## 11. Kod İstatistikleri

| Metrik | Değer |
|--------|-------|
| Backend Python dosyası | ~35 |
| Frontend TypeScript dosyası | ~12 |
| Toplam ajan | 6 |
| Toplam API uç noktası | 12 |
| Test dosyası | 14 |
| Toplam test kapsamı | %92 |
| Gömme vektörü boyutu | 512-d |
| pgvector indeks türü | HNSW (kosinüs) |
| Docker servisi | 2 (backend + db) |
| Alembic migration | 3 (init, pgvector, sighting) |
| Bağımlılık enjeksiyon yöntemi | FastAPI `Depends` + `lru_cache` |

---

## 12. Gelecek Geliştirmeler

| Öncelik | Geliştirme | Gerekçe |
|---------|-----------|---------|
| Yüksek | ArcFace ince ayar (SeaTurtleID2022) | Rank-1 doğruluğu %65+ hedefi |
| Yüksek | YOLO tabanlı baş tespiti | GrabCut'tan daha doğru segmentasyon |
| Orta | Celery/ARQ arka plan kuyruğu | Yüksek trafikte senkron gömme yetersiz kalır |
| Orta | JWT kimlik doğrulama | Üretim güvenliği |
| Düşük | PWA mobil uygulama | Saha araştırmacıları için çevrimdışı destek |
| Düşük | IUCN raporlama dışa aktarma | Standart koruma raporlaması |

ArcFace metrik öğrenme ile ince ayar başlatmak için:

```bash
python ml/training/train_arcface.py --dataset_dir data/SeaTurtleID2022/
```

---

## 13. Özet

| Prensip / Desen | Nerede Uygulandı | Sınıf / Dosya |
|-----------------|-----------------|---------------|
| **SRP** | Her ajan tek sorumluluk | `*_agent.py` × 6 |
| **OCP** | Segmentasyon stratejisi genişletilebilir | `SegmentationStrategy` ABC |
| **OCP** | Benzerlik metriği genişletilebilir | `SimilarityStrategy` ABC |
| **LSP** | Tüm ajanlar `BaseAgent.run()` ile kullanılabilir | `base_agent.py` |
| **ISP** | Repository'ler varlık bazında ayrılmış | `*_repository.py` × 3 |
| **DIP** | `embed_fn` callable enjeksiyonu | `FeatureExtractionAgent` |
| **Repository Pattern** | Tüm DB erişimi repository üzerinden | `photo_repository.py` |
| **Strategy Pattern** | Segmentasyon algoritması değiştirilebilir | `segmentation/` |
| **Strategy Pattern** | Benzerlik ölçütü değiştirilebilir | `SimilaritySearchAgent` |
| **Hata Sarma** | `AgentResult` + `_basarili_mi()` | `orchestrator_agent.py` |
| **DI Container** | `FastAPI Depends` + `lru_cache` | `core/container.py` |
| **Tip Güvenliği** | `Generic[TIn, TOut]` + dataclass | `BaseAgent`, tüm I/O |
