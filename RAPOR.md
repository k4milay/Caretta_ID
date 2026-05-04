# CarettaID — Teknik Rapor

**Proje:** CarettaID — Yapay Zeka Destekli Caretta Kaplumbağası Tanıma Sistemi  
**Geliştirici:** Kamil Ay (k4milay)  
**Tarih:** Mayıs 2026  

---

## 1. Projenin Amacı ve Kapsamı

Caretta caretta (adi deniz kaplumbağası) Akdeniz'de nesli tehlike altında olan bir türdür. Bireysel takip, popülasyon dinamiklerini anlamak ve koruma önlemleri almak için kritiktir. Geleneksel yöntemler (flipper etiketleme, deri örnekleme) hem hayvanı hem araştırmacıyı riske atar.

**CarettaID**, invazif olmayan fotoğraf tabanlı bir tanımlama sistemidir:

- Her kaplumbağanın **karapaks (kabuk) deseni** ve **baş leke örüntüsü** parmak izi gibi benzersizdir
- Sisteme yüklenen fotoğraf, kayıtlı tüm bireylerle karşılaştırılır
- Eşleşme bulunursa profil gösterilir; bulunmazsa yeni kayıt oluşturulur
- GPS gözlemleri ile bireysel hareket rotaları oluşturulur

---

## 2. Mimari Tasarım Kararları

### 2.1 Çoklu Ajan Mimarisi

Sistem, tek sorumluluk ilkesine dayalı birbirinden bağımsız ajanlardan oluşur:

| Ajan | Sorumluluk |
|------|-----------|
| `ImagePreprocessingAgent` | Görüntü doğrulama, normalleştirme, 3 bölge tespiti |
| `FeatureExtractionAgent` | EfficientNet-B0 ile ağırlıklı gömme vektörü üretimi |
| `SimilaritySearchAgent` | pgvector benzerlik araması, güven bantlama |
| `OrchestratorAgent` | Boru hattını yöneten koordinatör |
| `ProfileManagementAgent` | Kaplumbağa profili ve fotoğraf CRUD |
| `SightingTrackerAgent` | GPS gözlem kaydı ve GeoJSON rota üretimi |

**Neden LangGraph değil?** Ajanlar deterministik CV/DB boru hatlarıdır; LLM kontrol akışına gerek yoktur. Özel `BaseAgent[TIn, TOut]` tipi güvenlik sağlar ve LangGraph bağımlılığını ortadan kaldırır.

### 2.2 Vektör Veritabanı

Ayrı bir vektör DB (Qdrant, Weaviate) yerine tek PostgreSQL seçildi:
- pgvector HNSW indeksi <10ms ANN arama sağlar (≤100K fotoğraf)
- Altyapı karmaşıklığını azaltır
- Turtle ve Photo tabloları arasında yabancı anahtar bütünlüğü korunur

### 2.3 Üç Bölge Ağırlıklı Gömme

Sadece baş bölgesi yerine tam vücut analizi:

```
v_nihai = 0.30 × v_baş + 0.50 × v_karapaks + 0.20 × v_vücut
v_nihai = v_nihai / ||v_nihai||₂
```

**Gerekçe:**
- Karapaks deseni en ayırt edici özelliktir (%50 ağırlık)
- Baş lekeleri bireysel tanımlama için kritiktir (%30 ağırlık)
- Genel vücut şekli bağlamsal bilgi sağlar (%20 ağırlık)

---

## 3. SOLID ve Clean Code Uygulamaları

### 3.1 Tek Sorumluluk İlkesi (SRP)

Her ajan yalnızca bir sorumluluğa sahiptir:

```python
# PreprocessingAgent — SADECE görüntü hazırlığı
class ImagePreprocessingAgent(BaseAgent[PreprocessingInput, PreprocessingOutput]):
    async def _execute(self, payload):
        self._baytlari_dogrula(payload.image_bytes)   # Doğrulama
        goruntu = self._coz(payload.image_bytes)       # Çözme
        normallestirilmis = self._normallesтir(goruntu)  # Normalleştirme
        return PreprocessingOutput(...)
```

### 3.2 Açık/Kapalı İlkesi (OCP)

`SegmentationStrategy` arayüzü sayesinde yeni segmentasyon algoritmaları mevcut kodu değiştirmeden eklenebilir:

```python
class SegmentationStrategy(ABC):
    @abstractmethod
    def segment(self, image: np.ndarray) -> SegmentationResult: ...

# Yeni strateji eklemek için sadece bu sınıfı implement et:
class YOLOHeadStrategy(SegmentationStrategy):
    def segment(self, image): ...
```

### 3.3 Bağımlılık Enjeksiyonu (DIP)

`FeatureExtractionAgent` gerçek PyTorch fonksiyonuna değil, soyut bir callable'a bağlıdır:

```python
class FeatureExtractionAgent(BaseAgent[FeatureInput, FeatureOutput]):
    def __init__(self, embed_fn: EmbedFn = embed_image) -> None:
        self._embed = embed_fn  # Test ortamında sahte fonksiyon inject edilir
```

### 3.4 Repository Pattern

Tüm DB erişimi repository sınıfları üzerinden geçer:

```python
class PhotoRepository:
    async def upsert_embedding(self, photo_id, embedding) -> None: ...
    async def search_by_embedding(self, embedding, top_k) -> list[EmbeddingMatch]: ...
    async def list_by_turtle(self, turtle_id) -> list[Photo]: ...
```

Backing store değiştirilmek istendiğinde (örn. Qdrant'a geçiş) sadece bu dosya değişir.

---

## 4. Test Sonuçları

### 4.1 Birim Test Kapsamı (Faz 6 sonrası)

| Modül | Kapsam |
|-------|--------|
| `turtle_repository` | %100 |
| `sighting_repository` | %100 |
| `photo_repository` | %100 |
| `profile_management_agent` | %99 |
| `core/container` | %95 |
| **Toplam** | **%92** |

### 4.2 Tanımlama Doğruluğu

Model ince ayar yapılmadan (ImageNet ağırlıkları):
- Sentetik veri üzerinde Rank-1: ~%45–60 beklenen (tam vücut + 3 bölge)
- SeaTurtleID2022 veri seti üzerinde ince ayar sonrası: ≥%65 Rank-1 hedeflenmektedir

ArcFace metrik öğrenme ile ince ayar için:

```bash
python ml/training/train_arcface.py --dataset_dir data/SeaTurtleID2022/
```

---

## 5. Karşılaşılan Zorluklar ve Çözümler

### 5.1 pgvector Tip Uyuşmazlığı

**Sorun:** asyncpg, Python listesini pgvector `vector` tipine dönüştüremedi.

```
DataError: invalid input for query argument $1: [...] (expected str, got list)
```

**Çözüm:** Vektörü SQL literal string olarak formatla:

```python
# Hatalı:
{"vec": embedding.tolist(), "id": str(photo_id)}

# Doğru:
vec_literal = f"'[{','.join(str(x) for x in embedding.tolist())}]'"
text(f"UPDATE photos SET embedding = {vec_literal}::vector WHERE id = :id")
```

### 5.2 Docker İmaj Boyutu

**Sorun:** `torch==2.4.1` PyPI'dan indirilince CUDA kütüphaneleri (~3 GB) de indiriliyordu.

**Çözüm:** Dockerfile'da CPU-only PyTorch'u önce yükle:

```dockerfile
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
    torch==2.4.1+cpu torchvision==0.19.1+cpu
```

### 5.3 lru_cache Singleton ve Test İzolasyonu

**Sorun:** `lru_cache` ile sarılmış ajan singletonları `dependency_overrides` ile geçersiz kılınamıyordu.

**Çözüm:** Orchestrator ve ProfileAgent fabrikalarının kendisini override ederek bağımlılıkları doğrudan enjekte etmek.

---

## 6. Gelecek Geliştirmeler

| Öncelik | Geliştirme | Gerekçe |
|---------|-----------|---------|
| Yüksek | ArcFace ince ayar (SeaTurtleID2022) | Rank-1 doğruluğu %65+ hedefi |
| Yüksek | YOLO tabanlı baş tespiti | GrabCut'tan daha doğru baş segmentasyonu |
| Orta | Celery/ARQ arka plan kuyruğu | Yüksek trafikte senkron gömme yetersiz kalır |
| Orta | JWT kimlik doğrulama | Üretim güvenliği |
| Düşük | PWA mobil uygulama | Saha araştırmacıları için çevrimdışı destek |
| Düşük | Veri seti dışa aktarma | IUCN raporlama formatı |
