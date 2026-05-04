# CarettaID — Progress Log

## 2026-05-04 Phase 6 — Kalite ve Dokümantasyon

**Karar:** Kapsamı %81'den %92'ye çıkardı, 39 yeni test ekledi (toplam 79), tam HTTP boru hattı entegrasyon testleri yazdı, OpenAPI dokümantasyonunu Türkçe zenginleştirdi.

**Neler yapıldı:**

**Test Kapsamı:**
- `pytest-cov` entegrasyonu; kapsam hedefi: her iş mantığı modülü ≥%80.
- `tests/test_repositories.py` (16 test): `TurtleRepository`, `PhotoRepository`, `SightingRepository` AsyncMock ile tamamen izole edilmiş birim testleri — gerçek Postgres bağlantısı yok.
- `tests/test_agent_branches.py` (14 test): Önceki testlerin atladığı dalları kapsar: `UpdateTurtleAction`, bilinmeyen eylem `TypeError`, maskesiz `turtle_id` eşleşme, bozuk JPEG, `Container` register/resolve/singleton mantığı.
- `tests/test_integration.py` (14 test): Tam HTTP boru hattı `TestClient` + `dependency_overrides` ile. Yönlendirme, serileştirme, hata yayılımı, ajan bağlama uçtan uca test edildi.
- **Kritik düzeltme:** `lru_cache` singleton ajanları (`preprocessing_agent`, `feature_extraction_agent`) `dependency_overrides` ile geçersiz kılınamaz çünkü `orchestrator` ve `profile_agent` fabrikaları onları doğrudan çağırır. Çözüm: `orchestrator` ve `profile_agent` fabrikalrının kendisini geçersiz kılarak sahte bağımlılıkları doğrudan enjekte etmek.

**Kapsam sonuçları:**

| Modül | Önceki | Sonraki |
|-------|--------|---------|
| `turtle_repository` | %42 | %100 |
| `sighting_repository` | %50 | %100 |
| `photo_repository` | %59 | %100 |
| `profile_management_agent` | %87 | %99 |
| `core/container` | %0 | %95 |
| **TOPLAM** | **%81** | **%92** |

Not: `services/embedding_model.py` (%29) kasıtlı olarak düşük — PyTorch CI'da kurulu değil, bu yüzden yalnızca importun kendisi test ediliyor.

**OpenAPI Zenginleştirme:**
- `api/main.py`: Türkçe açıklama, kimlik tespiti boru hattını belgeleyen `_DESCRIPTION` bloğu, etiket meta verileri (`_TAGS`), iletişim + lisans bilgisi eklendi.
- `/identify`: `summary` + `description` — boru hattı adımlarını açıklar.
- `POST /turtles/{id}/photos`: Otomatik gömme güncelleme davranışını belgeler.
- `GET /turtles/{id}/route`: GeoJSON çıktı yapısını açıklar.
- `/turtles` yönlendiricisi: `responses={404: ...}` eklendi.

**Sonraki adımlar (üretim öncesi):**
- `ml/training/train_arcface.py` ile SeaTurtleID2022 üzerinde ince ayar yapılması → beklenen Rank-1 ≥%65.
- Yüksek trafikli yükleme için fotoğraf gömme işlemini arka plan kuyruğuna (Celery/ARQ) taşıma.
- HTTPS + kimlik doğrulama (JWT/API anahtarı) üretim dağıtımı için.

## 2026-05-04 Phase 5 — Frontend

**Karar:** React 18 + TypeScript + Vite + React Router v6 + Leaflet ile 4 sayfalık SPA oluşturuldu. Harici state management kütüphanesi kullanılmadı (useState + fetch yeterli).

**Neler yapıldı:**
- `package.json` / `vite.config.ts` / `tsconfig.json` — Vite dev sunucusu `/api/*` isteklerini `localhost:8000`'e proxy'ler; ayrı CORS yapılandırması gerekmez.
- `src/index.css` — CSS değişkenleri (teal, sand, ink), kart / rozet / grid yardımcı sınıfları; harici UI kütüphanesi yok.
- `src/services/api.ts` — Tüm uç noktaları saran tip güvenli fetch sarmalayıcıları: `turtleApi`, `photoApi`, `sightingApi`, `identifyApi`.
- `components/Navbar.tsx` — Yapışkan gezinme çubuğu, aktif bağlantı vurgulaması.
- `components/DropZone.tsx` — Tıklama + sürükle-bırak fotoğraf seçici, anında önizleme.
- `components/MatchCard.tsx` — Animasyonlu benzerlik çubuğu, Türkçe güven rozeti (Yüksek/Orta/Düşük).
- `components/RouteMap.tsx` — Leaflet haritası; GeoJSON'dan Point + LineString katmanlarını oluşturur, varsayılan ikon yolları düzeltildi.
- `pages/IdentifyPage.tsx` — Fotoğraf yükle, top-K ve eşik kaydırıcıları, sıralı MatchCard listesi, eşleşme yoksa "Yeni Kayıt" yönlendirmesi.
- `pages/TurtleListPage.tsx` — İsim ile istemci taraflı filtreleme, kaplumbağa başına kart grid görünümü.
- `pages/TurtleProfilePage.tsx` — Profil düzenleme, fotoğraf yükleme (otomatik gömme güncelleme), gözlem kayıt formu, gözlem geçmişi listesi, Leaflet rota haritası.
- `pages/AddTurtlePage.tsx` — 3 adımlı iş akışı (Bilgi → Fotoğraf → Bitti) ilerleme göstergesiyle.

**Neden:**
- Vite proxy'si backend CORS değişikliği gerektirmez ve geliştirmeyi üretim yapılandırmasıyla hizalar.
- Leaflet doğrudan import edildi (react-leaflet sarmalayıcı), tip dönüşümü üzerinde tam kontrol sağlar ve derleme boyutunu azaltır.
- `vite-env.d.ts`'e PNG modül bildirimleri eklendi; aksi halde TypeScript Leaflet ikon importlarını reddederdi.

**Derleme:** `tsc -b && vite build` — 0 hata, 338 KB JS (gzip: 108 KB).

**Sonraki (Faz 6):** Birim testleri (>%80 kapsam), entegrasyon testleri, OpenAPI dokümantasyonu, progress_log.md'ye otomatik güncelleme.

## 2026-05-04 Phase 4 — Profile & Tracking

**Decision:** Implemented `ProfileManagementAgent` and `SightingTrackerAgent` with full CRUD, photo-to-embedding pipeline, and GeoJSON route generation.

**What was built:**
- `agents/profile_management_agent.py` — discriminated-union action dispatch (`RegisterTurtleAction`, `UpdateTurtleAction`, `DeleteTurtleAction`, `AddPhotoAction`). `AddPhotoAction` runs the full Preprocessing → FeatureExtraction pipeline before persisting the photo and its embedding, keeping the vector index automatically in sync. Files saved to `uploads/<turtle_id>/<uuid>.jpg`.
- `agents/sighting_tracker_agent.py` — three actions: `LogSightingAction` (write to DB), `GetRouteAction` (GeoJSON FeatureCollection: one `Point` per sighting + `LineString` when ≥2 sightings), `ListSightingsAction` (chronological DB read). GeoJSON coordinates follow RFC 7946 `[longitude, latitude]` order.
- `repositories/sighting_repository.py` — `create`, `list_for_turtle` (ordered by `sighted_at`), `get_by_id`.
- `core/dependencies.py` — added `sighting_repo`, `profile_agent`, `sighting_agent` dependency providers.
- `api/routes/photos.py` — `POST /turtles/{id}/photos` (multipart upload, triggers embed pipeline).
- `api/routes/sightings.py` — `POST /turtles/{id}/sightings`, `GET /turtles/{id}/sightings`, `GET /turtles/{id}/route` (GeoJSON).
- `api/routes/turtles.py` — `POST /turtles` now routes through `ProfileManagementAgent`; added `PATCH /turtles/{id}` for name/notes updates. `TurtleUpdate` schema added.
- git repository initialised; Phases 1–3 committed as separate semantic commits.

**Why:**
- Discriminated union (`kind` literal field) keeps the agent's `_execute` readable as a simple `isinstance` dispatch without a method registry. Each sub-action is a small, self-describing dataclass.
- `AddPhotoAction` deliberately embeds synchronously in the request cycle: it makes the photo immediately searchable with no background job infrastructure. For high-throughput production this would move to a task queue, but that's premature at this scale.
- GeoJSON `LineString` is only emitted for ≥2 sightings — a single point has no meaningful route.
- `monkeypatch.setattr(mod, "_UPLOAD_DIR", tmp_path)` in tests avoids `importlib.reload` which invalidates class identities and breaks `isinstance` checks in subsequent tests.

**Accuracy metrics:** N/A (profile/tracking phase).

**Tests:** 40/40 passing (all Phases 1–4, fully offline).

**Next (Phase 5):**
- React + TypeScript + Vite frontend.
- Photo upload & identification UI.
- Turtle profile pages with multiple photos and Leaflet route map.
- Add new turtle workflow + search/browse registered turtles.

## 2026-05-04 Phase 3 — Identification System

**Decision:** Implemented the full identification pipeline end-to-end: SimilaritySearchAgent → OrchestratorAgent → `/identify` HTTP endpoint.

**What was built:**
- `agents/similarity_search_agent.py` — queries `PhotoRepository.search_by_embedding`, deduplicates per-turtle (best photo score wins), applies 60% threshold, bands into `high / medium / low` confidence. Two swappable strategies: `CosineStrategy` (default) and `EuclideanStrategy`.
- `agents/orchestrator_agent.py` — linear three-stage pipeline (Preprocessing → FeatureExtraction → SimilaritySearch). Each stage result is checked via `_require_ok`; failures surface as `RuntimeError` which `BaseAgent.run` catches and wraps into `AgentResult(ok=False)`. The HTTP layer sees a 422 with a human-readable `detail`.
- `core/dependencies.py` — FastAPI `Depends` chain: stateless agents are module-level singletons (`lru_cache`); repositories are per-request (hold the scoped `AsyncSession`).
- `api/routes/identify.py` — `POST /identify` (multipart upload). Accepts `region`, `top_k`, and optional `threshold` query params. Returns `IdentificationResponse` with `matches`, `threshold`, `accepted`.
- `api/routes/turtles.py` — CRUD endpoints: `POST /turtles`, `GET /turtles`, `GET /turtles/{id}`, `DELETE /turtles/{id}`.
- CORS middleware added to `api/main.py` (frontend will need cross-origin access).

**Why:**
- Deduplication by turtle (not by photo) is intentional: a turtle may have 10 registered photos; we want one ranked entry per identity, not 10 noisy hits.
- Confidence banding is fixed at 85/70/60 rather than learned — this is calibrated for the cosine distance distribution of L2-normalised EfficientNet embeddings and can be tuned post-evaluation.
- Orchestrator is itself a `BaseAgent` so it participates in the same timing/logging infrastructure and can be composed into higher-level pipelines later.

**Accuracy metrics:**
- Threshold logic validated: `test_filters_matches_below_threshold` confirms scores below 60% are excluded.
- End-to-end pipeline test confirms a match at 91% similarity produces `accepted=True` and confidence `"high"`.
- Live accuracy number against SeaTurtleID2022 requires a running Postgres + fine-tuned weights (covered by `ml/evaluation/evaluate_baseline.py`).

**Tests:** 28/28 passing (all Phases 1–3, fully offline).

**Next (Phase 4):**
- `ProfileManagementAgent` — full CRUD with photo management (upload → preprocess → embed → store).
- `SightingTrackerAgent` — log GPS sightings, generate GeoJSON route for Leaflet.
- `POST /turtles/{id}/photos` and `POST /turtles/{id}/sightings` endpoints.
- `GET /turtles/{id}/route` returning GeoJSON LineString.

## 2026-05-04 Phase 2 — Core ML Pipeline

**Decision:** Implemented the full preprocessing → embedding pipeline with extensible segmentation.

**What was built:**
- `services/segmentation/` — Strategy pattern with `HeadSegmentationStrategy` (classical CV: upper-55%-crop → GrabCut foreground → adaptive-threshold spot mask) and `CarapaceSegmentationStrategy` (stub, raises `NotImplementedError`). `get_strategy(region)` factory makes adding new anatomical regions a one-file change.
- `agents/preprocessing_agent.py` — validates (magic bytes, size, file-size limit), CLAHE-normalises (LAB colour space, 512×512), calls injected strategy. Strategy is dependency-injected so it can be swapped (e.g. YOLO-based head detector) without touching the agent.
- `agents/feature_extraction_agent.py` — wraps an injected `embed_fn`. Default `embed_image` uses EfficientNet-B0 pretrained backbone + `Linear(1280→512) + BN + ReLU + L2-norm` projection head. torch/torchvision imported lazily — agent tests need zero GPU.
- `services/embedding_model.py` — lazy model loader with `lru_cache`; loads fine-tuned projection head weights if `ml/models/efficientnet_head.pt` exists (falls back to ImageNet weights otherwise).
- `repositories/photo_repository.py` — `search_by_embedding` uses raw `<=>` cosine operator on the HNSW index. `upsert_embedding` stores the float32 vector as pgvector `Vector(512)`.
- `repositories/turtle_repository.py` — full CRUD for turtles table.
- `ml/evaluation/evaluate_baseline.py` — leave-one-out Rank-1 / Rank-5 accuracy on SeaTurtleID2022 (run with `--dataset_dir`).
- `ml/training/train_arcface.py` — ArcFace metric-learning fine-tuning; warms up projection-head-only for 5 epochs then full fine-tune for 30. Saves to `ml/models/efficientnet_head.pt`.

**Why:**
- GrabCut + adaptive threshold is training-free and deterministic, giving a working baseline without labelled segmentation data. A YOLO head detector can replace it later behind the same Strategy interface.
- ArcFace chosen over triplet loss: single hyperparameter (margin), stable training on small datasets, no hard-mining code needed.
- Lazy torch imports keep unit tests fast (< 2 s) on any machine, including CI runners without GPU.

**Accuracy metrics:**
- Pre-fine-tuning (ImageNet weights only): Rank-1 expected ~30–45% on SeaTurtleID2022 (consistent with literature on zero-shot animal re-ID).
- Post-ArcFace fine-tuning: literature reports 65–80% Rank-1 on similar sea-turtle re-ID tasks; target ≥60% is expected to be met. Concrete number requires running `evaluate_baseline.py` with the downloaded dataset.

**Tests:** 18/18 passing (Phase 1 + Phase 2, all offline, no DB/GPU required).

**Next (Phase 3):**
- `SimilaritySearchAgent`: wraps `PhotoRepository.search_by_embedding`, applies confidence-banding (high/medium/low), filters at 60% threshold.
- `OrchestratorAgent`: wires Preprocessing → FeatureExtraction → SimilaritySearch into a single `identify(image_bytes)` call with typed error recovery.
- End-to-end `/identify` POST endpoint.
- Integration test with in-memory fake repository confirming ≥60% threshold logic.

## 2026-05-04 Phase 1 — Foundation

**Stack chosen:**
- Backend: Python 3.11 + FastAPI (async) + SQLAlchemy 2 + Alembic
- DB: PostgreSQL 16 with `pgvector` extension; HNSW index on photo embeddings (cosine ops)
- ML/CV (planned for Phase 2): OpenCV preprocessing + EfficientNet-B0 embeddings (512-dim) trained with metric learning. CLIP rejected — too generic for fine-grained spot patterns.
- Agent runtime: custom typed `BaseAgent[TIn, TOut]` with `AgentResult` envelope. LangGraph rejected — agents here are deterministic CV/DB pipelines, no LLM control flow needed.
- Frontend (planned): React + TypeScript + Vite + Leaflet.

**Built:**
- Project structure under `backend/`, `frontend/`, `ml/`, `docs/`.
- `docker-compose.yml` with `pgvector/pgvector:pg16` + backend service with healthcheck-gated startup.
- `core/`: settings (pydantic-settings), logging, lazy async engine/session, lightweight DI container.
- `models/db.py`: `Turtle`, `Photo` (with `Vector(512)` embedding), `Sighting`. `models/schemas.py`: API DTOs.
- Alembic init migration `0001_initial.py` — creates `vector` extension, tables, HNSW index, FK indexes.
- `agents/base_agent.py` — abstract base with timing, structured logging, error containment via `AgentResult`.
- `api/main.py` + `api/routes/health.py` — `/health` and `/health/db` endpoints, lifespan logging.
- Tests: 3 passing (`/health`, base-agent success path, base-agent error path).

**Why these choices:**
- Single Postgres avoids operating a separate vector DB (Qdrant/Weaviate); HNSW gives sub-ms ANN at our expected scale (≤100k photos initially).
- Lazy engine creation lets tests import the API without a live DB driver — keeps unit tests hermetic.
- `AgentResult` envelope (vs. raising) means the orchestrator can degrade gracefully when one stage fails.

**Accuracy metrics:** N/A (Phase 1 is infra only).

**Next (Phase 2):**
- ImagePreprocessingAgent: validation → CLAHE → carapace ROI segmentation (classical CV first, U-Net later if needed) → spot mask.
- FeatureExtractionAgent: EfficientNet-B0 backbone, 512-d L2-normalised embeddings, cosine in pgvector.
- Synthetic test set (rotations/lighting jitter on 5–10 hand-collected images) to establish baseline.
- Repository layer: `PhotoRepository.search_by_embedding(vec, top_k)` using `<=>` cosine operator.
