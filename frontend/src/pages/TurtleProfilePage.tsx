import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import RouteMap from "../components/RouteMap";
import DropZone from "../components/DropZone";
import {
  turtleApi, photoApi, sightingApi,
  type Turtle, type Photo, type Sighting, type GeoJSON,
} from "../services/api";

const COLORS = ["#0d9488","#0891b2","#7c3aed","#db2777","#ea580c","#16a34a"];
const avatarColor = (name: string) => COLORS[name.charCodeAt(0) % COLORS.length];

function StatBadge({ icon, value, label }: { icon: string; value: string | number; label: string }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: "1.1rem", marginBottom: ".15rem" }}>{icon}</div>
      <div style={{ fontSize: "1.25rem", fontWeight: 900, color: "#0f172a", letterSpacing: "-.02em" }}>{value}</div>
      <div style={{ fontSize: ".72rem", color: "#64748b", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".06em" }}>{label}</div>
    </div>
  );
}

export default function TurtleProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [turtle,       setTurtle]       = useState<Turtle | null>(null);
  const [photos,       setPhotos]       = useState<Photo[]>([]);
  const [sightings,    setSightings]    = useState<Sighting[]>([]);
  const [geojson,      setGeojson]      = useState<GeoJSON | null>(null);
  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState("");

  const [photoFile,    setPhotoFile]    = useState<File | null>(null);
  const [uploading,    setUploading]    = useState(false);
  const [uploadMsg,    setUploadMsg]    = useState<{ok:boolean;text:string}|null>(null);

  const [lat,          setLat]          = useState("");
  const [lon,          setLon]          = useState("");
  const [locName,      setLocName]      = useState("");
  const [loggingSight, setLoggingSight] = useState(false);
  const [sightMsg,     setSightMsg]     = useState<{ok:boolean;text:string}|null>(null);

  const [editing,      setEditing]      = useState(false);
  const [editName,     setEditName]     = useState("");
  const [editNotes,    setEditNotes]    = useState("");
  const [saving,       setSaving]       = useState(false);

  const [activeTab,    setActiveTab]    = useState<"gallery"|"photos"|"sightings">("gallery");
  const [lightbox,     setLightbox]     = useState<string | null>(null);
  const [deletingId,   setDeletingId]   = useState<string | null>(null);

  useEffect(() => { if (id) load(); }, [id]);

  async function load() {
    setLoading(true);
    try {
      const [t, p, s, g] = await Promise.all([
        turtleApi.get(id!),
        photoApi.list(id!),
        sightingApi.list(id!),
        sightingApi.route(id!).catch(() => null),
      ]);
      setTurtle(t); setEditName(t.name); setEditNotes(t.notes ?? "");
      setPhotos(p); setSightings(s); setGeojson(g);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Yüklenemedi");
    } finally { setLoading(false); }
  }

  async function handlePhotoUpload() {
    if (!photoFile || !id) return;
    setUploading(true); setUploadMsg(null);
    try {
      const newPhoto = await photoApi.upload(id, photoFile);
      setPhotos(prev => [newPhoto, ...prev]);
      setUploadMsg({ ok: true, text: "Fotoğraf yüklendi ve gömme vektörü güncellendi." });
      setPhotoFile(null);
      setActiveTab("gallery");
    } catch (e) {
      setUploadMsg({ ok: false, text: e instanceof Error ? e.message : "Hata" });
    } finally { setUploading(false); }
  }

  async function handleLogSighting() {
    if (!id || !lat || !lon) return;
    setLoggingSight(true); setSightMsg(null);
    try {
      const s = await sightingApi.log(id, { latitude: parseFloat(lat), longitude: parseFloat(lon), location_name: locName || undefined });
      setSightings(prev => [...prev, s]);
      setGeojson(await sightingApi.route(id).catch(() => null));
      setLat(""); setLon(""); setLocName("");
      setSightMsg({ ok: true, text: "Gözlem kaydedildi." });
    } catch (e) {
      setSightMsg({ ok: false, text: e instanceof Error ? e.message : "Hata" });
    } finally { setLoggingSight(false); }
  }

  async function handleSave() {
    if (!id) return;
    setSaving(true);
    try {
      const updated = await turtleApi.update(id, { name: editName, notes: editNotes });
      setTurtle(updated); setEditing(false);
    } finally { setSaving(false); }
  }

  async function handleDelete() {
    if (!id || !confirm(`"${turtle?.name}" silinsin mi? Bu işlem geri alınamaz.`)) return;
    await turtleApi.delete(id);
    navigate("/turtles");
  }

  async function handleDeletePhoto(photoId: string) {
    if (!id || deletingId) return;
    setDeletingId(photoId);
    try {
      await photoApi.delete(id, photoId);
      setPhotos(prev => prev.filter(p => p.id !== photoId));
    } finally { setDeletingId(null); }
  }

  if (loading) return <div className="page empty"><div className="spinner" style={{ margin: "0 auto" }} /></div>;
  if (error)   return <div className="page"><div className="card" style={{ color: "var(--danger)" }}>{error}</div></div>;
  if (!turtle) return null;

  const ac = avatarColor(turtle.name);
  const sonGozlem = sightings.length > 0 ? sightings[sightings.length - 1] : null;

  return (
    <div>
      {/* Lightbox */}
      {lightbox && (
        <div onClick={() => setLightbox(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.88)", zIndex: 999, display: "flex", alignItems: "center", justifyContent: "center", cursor: "zoom-out" }}>
          <img src={lightbox} alt="büyük görünüm" style={{ maxWidth: "90vw", maxHeight: "90vh", borderRadius: 16, boxShadow: "0 24px 80px rgba(0,0,0,.6)" }} />
        </div>
      )}

      {/* ── Profile banner ── */}
      <div style={{
        background: `linear-gradient(145deg, #0a2540 0%, ${ac}cc 60%, ${ac} 100%)`,
        padding: "3rem 2rem 6rem",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{ position: "absolute", width: 500, height: 500, borderRadius: "50%", background: "rgba(255,255,255,.04)", top: -150, right: -100, pointerEvents: "none" }} />

        <div style={{ maxWidth: 1080, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1.5rem", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
              {photos.length > 0 ? (
                <img src={photoApi.url(photos[0].file_path)} alt={turtle.name}
                  style={{ width: 88, height: 88, borderRadius: "50%", objectFit: "cover", border: "3px solid rgba(255,255,255,.5)", boxShadow: "0 8px 28px rgba(0,0,0,.35)", flexShrink: 0, cursor: "pointer" }}
                  onClick={() => setLightbox(photoApi.url(photos[0].file_path))}
                  onError={e => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              ) : (
                <div style={{ width: 88, height: 88, borderRadius: "50%", background: "rgba(255,255,255,.2)", backdropFilter: "blur(8px)", border: "3px solid rgba(255,255,255,.4)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "2.2rem", fontWeight: 900, color: "#fff", flexShrink: 0 }}>
                  {turtle.name.charAt(0).toUpperCase()}
                </div>
              )}

              <div>
                <p style={{ fontSize: ".7rem", fontWeight: 800, color: "rgba(255,255,255,.65)", textTransform: "uppercase", letterSpacing: ".1em", marginBottom: ".3rem" }}>
                  Kaplumbağa Profili
                </p>
                {editing
                  ? <input value={editName} onChange={e => setEditName(e.target.value)}
                      style={{ fontSize: "1.8rem", fontWeight: 900, background: "rgba(255,255,255,.15)", border: "2px solid rgba(255,255,255,.4)", borderRadius: 10, padding: ".3rem .7rem", color: "#fff", width: "auto", backdropFilter: "blur(8px)" }} />
                  : <h1 style={{ fontSize: "2rem", fontWeight: 900, color: "#fff", letterSpacing: "-.03em", lineHeight: 1.1 }}>{turtle.name}</h1>
                }
                {sonGozlem?.location_name && (
                  <div style={{ fontSize: ".82rem", color: "rgba(255,255,255,.65)", marginTop: ".4rem" }}>
                    📍 Son görüldüğü yer: <strong style={{ color: "rgba(255,255,255,.9)" }}>{sonGozlem.location_name}</strong>
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: "flex", gap: ".6rem" }}>
              {editing
                ? <>
                    <button className="btn-primary" onClick={handleSave} disabled={saving} style={{ borderRadius: 10, fontSize: ".875rem" }}>{saving ? "…" : "Kaydet"}</button>
                    <button onClick={() => setEditing(false)} style={{ background: "rgba(255,255,255,.15)", border: "1.5px solid rgba(255,255,255,.3)", color: "#fff", borderRadius: 10, padding: ".45rem 1rem", fontSize: ".875rem", backdropFilter: "blur(8px)" }}>İptal</button>
                  </>
                : <>
                    <button onClick={() => setEditing(true)} style={{ background: "rgba(255,255,255,.15)", border: "1.5px solid rgba(255,255,255,.3)", color: "#fff", borderRadius: 10, padding: ".45rem 1rem", fontSize: ".875rem", backdropFilter: "blur(8px)", cursor: "pointer" }}>Düzenle</button>
                    <button className="btn-danger" onClick={handleDelete} style={{ borderRadius: 10, fontSize: ".875rem", background: "rgba(239,68,68,.2)", borderColor: "rgba(239,68,68,.5)", color: "#fca5a5" }}>Sil</button>
                  </>
              }
            </div>
          </div>
        </div>
      </div>

      <div className="page" style={{ marginTop: "-4.5rem", paddingTop: 0 }}>

        {/* ── Stats bar ── */}
        <div style={{ background: "#fff", borderRadius: 20, padding: "1.25rem 2rem", marginBottom: "1.25rem", boxShadow: "0 20px 60px rgba(12,74,110,.15)", border: "1px solid rgba(255,255,255,.9)", display: "flex", gap: "2rem", justifyContent: "space-around", flexWrap: "wrap" }}>
          <StatBadge icon="📷" value={photos.length}    label="Fotoğraf" />
          <div style={{ width: 1, background: "#f1f5f9" }} />
          <StatBadge icon="📍" value={sightings.length} label="Gözlem" />
          <div style={{ width: 1, background: "#f1f5f9" }} />
          <StatBadge icon="📅" value={new Date(turtle.registered_at).toLocaleDateString("tr-TR", { month: "short", year: "numeric" })} label="Kayıt" />
        </div>

        {/* ── Notes (edit mode) ── */}
        {editing && (
          <div className="card" style={{ marginBottom: "1.25rem", borderRadius: 18 }}>
            <label>Notlar</label>
            <textarea rows={3} value={editNotes} onChange={e => setEditNotes(e.target.value)} placeholder="Gözlem notları, ayırt edici özellikler…" />
          </div>
        )}

        {/* ── Notes (view mode) ── */}
        {!editing && turtle.notes && (
          <div style={{ background: "linear-gradient(135deg,#f0fdfa,#e0f2fe)", border: "1.5px solid #99f6e4", borderRadius: 18, padding: "1.1rem 1.4rem", marginBottom: "1.25rem", color: "#0f172a", fontSize: ".92rem", lineHeight: 1.7 }}>
            {turtle.notes}
          </div>
        )}

        {/* ── Map ── */}
        <div style={{ background: "#fff", border: "1px solid rgba(226,232,240,.6)", borderRadius: 22, overflow: "hidden", marginBottom: "1.25rem", boxShadow: "var(--shadow-md)" }}>
          <div style={{ padding: "1rem 1.5rem", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 700, fontSize: ".95rem", color: "#0f172a" }}>🗺 Hareket Rotası</span>
            {sightings.length > 0 && <span style={{ fontSize: ".8rem", color: "#64748b" }}>{sightings.length} gözlem noktası</span>}
          </div>
          <RouteMap geojson={geojson} />
          {!geojson && (
            <p style={{ padding: "1rem 1.5rem", color: "#94a3b8", fontSize: ".85rem" }}>Rota için en az 2 gözlem gereklidir.</p>
          )}
        </div>

        {/* ── Tabs ── */}
        <div style={{ display: "inline-flex", gap: ".2rem", marginBottom: "1.25rem", background: "#fff", border: "1px solid rgba(226,232,240,.6)", borderRadius: 15, padding: ".3rem", boxShadow: "var(--shadow)" }}>
          {([
            { key: "gallery",   label: `📷 Galeri (${photos.length})` },
            { key: "photos",    label: "➕ Fotoğraf Ekle" },
            { key: "sightings", label: "📍 Gözlem Ekle" },
          ] as const).map(({ key, label }) => (
            <button key={key} onClick={() => setActiveTab(key)}
              style={{
                padding: ".45rem 1.15rem", borderRadius: 11,
                fontWeight: activeTab === key ? 700 : 500,
                fontSize: ".875rem", border: "none", cursor: "pointer",
                transition: "all .18s cubic-bezier(.4,0,.2,1)",
                background: activeTab === key ? `linear-gradient(135deg,#0d9488,#0891b2)` : "transparent",
                color: activeTab === key ? "#fff" : "#64748b",
                boxShadow: activeTab === key ? "0 2px 10px rgba(13,148,136,.28)" : "none",
              }}>
              {label}
            </button>
          ))}
        </div>

        {/* ── Gallery ── */}
        {activeTab === "gallery" && (
          <div className="card scale-in" style={{ borderRadius: 20 }}>
            {photos.length === 0 ? (
              <div style={{ textAlign: "center", padding: "3rem" }}>
                <div style={{ fontSize: "3.5rem", marginBottom: "1rem", opacity: .2 }}>📷</div>
                <p style={{ fontWeight: 700, marginBottom: ".5rem" }}>Henüz fotoğraf yok</p>
                <button className="btn-primary" style={{ marginTop: ".75rem", borderRadius: 10 }} onClick={() => setActiveTab("photos")}>Fotoğraf Ekle</button>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(165px,1fr))", gap: "1rem" }}>
                {photos.map((p, i) => (
                  <div key={p.id} style={{ position: "relative", borderRadius: 14, overflow: "hidden", aspectRatio: "1", boxShadow: "var(--shadow)", border: "1px solid #f1f5f9" }}>
                    <img src={photoApi.url(p.file_path)} alt={`fotoğraf ${i+1}`}
                      style={{ width: "100%", height: "100%", objectFit: "cover", cursor: "zoom-in", transition: "transform .22s cubic-bezier(.4,0,.2,1)" }}
                      onClick={() => setLightbox(photoApi.url(p.file_path))}
                      onMouseEnter={e => (e.currentTarget.style.transform = "scale(1.05)")}
                      onMouseLeave={e => (e.currentTarget.style.transform = "")}
                      onError={e => { (e.currentTarget.parentElement!.style.background = "#f1f5f9"); (e.currentTarget.style.display = "none"); }}
                    />
                    {i === 0 && (
                      <span style={{ position: "absolute", top: 8, left: 8, background: "#0d9488", color: "#fff", fontSize: ".62rem", fontWeight: 800, padding: ".15rem .5rem", borderRadius: 99, letterSpacing: ".04em" }}>ANA</span>
                    )}
                    <button onClick={() => handleDeletePhoto(p.id)} disabled={deletingId === p.id}
                      style={{ position: "absolute", top: 8, right: 8, width: 28, height: 28, borderRadius: "50%", background: "rgba(220,38,38,.88)", border: "none", color: "#fff", fontSize: ".85rem", fontWeight: 900, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", backdropFilter: "blur(4px)" }}>
                      {deletingId === p.id ? "…" : "×"}
                    </button>
                    <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "linear-gradient(transparent,rgba(0,0,0,.55))", padding: ".4rem .6rem", pointerEvents: "none" }}>
                      <div style={{ fontSize: ".68rem", color: "rgba(255,255,255,.85)" }}>{new Date(p.uploaded_at).toLocaleDateString("tr-TR")}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Upload tab ── */}
        {activeTab === "photos" && (
          <div className="card scale-in" style={{ borderRadius: 20 }}>
            <div className="section-label">Yeni Fotoğraf Yükle</div>
            <DropZone onFile={setPhotoFile} />
            {photoFile && (
              <button className="btn-primary" style={{ marginTop: "1rem", width: "100%", borderRadius: 11 }} onClick={handlePhotoUpload} disabled={uploading}>
                {uploading ? "Yükleniyor…" : "Fotoğrafı Yükle"}
              </button>
            )}
            {uploadMsg && (
              <div style={{ marginTop: ".75rem", fontSize: ".88rem", padding: ".65rem 1rem", borderRadius: 10, background: uploadMsg.ok ? "#f0fdf4" : "#fef2f2", color: uploadMsg.ok ? "#15803d" : "#dc2626" }}>
                {uploadMsg.text}
              </div>
            )}
          </div>
        )}

        {/* ── Sightings tab ── */}
        {activeTab === "sightings" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            <div className="card scale-in" style={{ borderRadius: 20 }}>
              <div className="section-label">Yeni Gözlem Ekle</div>
              <div className="grid-2" style={{ gap: ".75rem", marginBottom: ".75rem" }}>
                <div><label>Enlem</label><input type="number" step="any" placeholder="36.5" value={lat} onChange={e => setLat(e.target.value)} /></div>
                <div><label>Boylam</label><input type="number" step="any" placeholder="28.0" value={lon} onChange={e => setLon(e.target.value)} /></div>
              </div>
              <label>Konum Adı (opsiyonel)</label>
              <input placeholder="Datça, Türkiye" value={locName} onChange={e => setLocName(e.target.value)} style={{ marginBottom: ".85rem" }} />
              <button className="btn-primary" style={{ width: "100%", borderRadius: 11 }} onClick={handleLogSighting} disabled={loggingSight || !lat || !lon}>
                {loggingSight ? "Kaydediliyor…" : "Gözlemi Kaydet"}
              </button>
              {sightMsg && (
                <div style={{ marginTop: ".75rem", fontSize: ".88rem", padding: ".65rem 1rem", borderRadius: 10, background: sightMsg.ok ? "#f0fdf4" : "#fef2f2", color: sightMsg.ok ? "#15803d" : "#dc2626" }}>
                  {sightMsg.text}
                </div>
              )}
            </div>

            {sightings.length > 0 && (
              <div className="card" style={{ borderRadius: 20 }}>
                <div className="section-label">Gözlem Geçmişi ({sightings.length})</div>
                <div style={{ display: "flex", flexDirection: "column", gap: ".5rem" }}>
                  {[...sightings].reverse().map((s, i) => (
                    <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: ".8rem 1rem", borderRadius: 12, background: i === 0 ? "linear-gradient(135deg,#f0fdfa,#e0f2fe)" : "#f8fafc", border: i === 0 ? "1px solid #99f6e4" : "1px solid transparent" }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: ".9rem", color: "#0f172a" }}>{s.location_name ?? "Bilinmeyen konum"}</div>
                        <div style={{ fontSize: ".75rem", color: "#94a3b8", marginTop: ".1rem" }}>{s.latitude.toFixed(4)}°K, {s.longitude.toFixed(4)}°D</div>
                      </div>
                      <div style={{ fontSize: ".78rem", color: "#64748b", fontWeight: 600 }}>
                        {new Date(s.sighted_at).toLocaleDateString("tr-TR", { day: "numeric", month: "long" })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
