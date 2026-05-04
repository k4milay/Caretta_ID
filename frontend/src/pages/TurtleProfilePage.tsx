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

export default function TurtleProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [turtle,    setTurtle]    = useState<Turtle | null>(null);
  const [photos,    setPhotos]    = useState<Photo[]>([]);
  const [sightings, setSightings] = useState<Sighting[]>([]);
  const [geojson,   setGeojson]   = useState<GeoJSON | null>(null);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState("");

  const [photoFile,    setPhotoFile]    = useState<File | null>(null);
  const [uploading,    setUploading]    = useState(false);
  const [uploadMsg,    setUploadMsg]    = useState<{ok:boolean;text:string}|null>(null);

  const [lat,          setLat]          = useState("");
  const [lon,          setLon]          = useState("");
  const [locName,      setLocName]      = useState("");
  const [loggingSight, setLoggingSight] = useState(false);
  const [sightMsg,     setSightMsg]     = useState<{ok:boolean;text:string}|null>(null);

  const [editing,   setEditing]   = useState(false);
  const [editName,  setEditName]  = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [saving,    setSaving]    = useState(false);

  const [activeTab, setActiveTab] = useState<"gallery"|"photos"|"sightings">("gallery");
  const [lightbox,  setLightbox]  = useState<string | null>(null);

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
      setUploadMsg({ ok: true, text: "Fotoğraf yüklendi ve analiz vektörü güncellendi." });
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
      const s = await sightingApi.log(id, {
        latitude: parseFloat(lat), longitude: parseFloat(lon),
        location_name: locName || undefined,
      });
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

  // Fotoğraf URL'ini backend static endpoint'inden oluştur
  // file_path örneği: "uploads/uuid/uuid.jpg"
  function photoUrl(filePath: string): string {
    const normalized = filePath.replace(/\\/g, "/").replace(/^uploads\//, "");
    return `/api/static/uploads/${normalized}`;
  }

  if (loading) return (
    <div className="page empty">
      <div style={{ width: 34, height: 34, border: "3px solid var(--border)", borderTopColor: "var(--teal)", borderRadius: "50%", animation: "spin .7s linear infinite", margin: "0 auto" }} />
    </div>
  );
  if (error) return <div className="page"><div className="card" style={{ color: "var(--danger)" }}>{error}</div></div>;
  if (!turtle) return null;

  const ac = avatarColor(turtle.name);
  const sonGozlem = sightings.length > 0 ? sightings[sightings.length - 1] : null;

  return (
    <div className="page">
      {/* Lightbox */}
      {lightbox && (
        <div onClick={() => setLightbox(null)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.85)", zIndex: 999, display: "flex", alignItems: "center", justifyContent: "center", cursor: "zoom-out" }}>
          <img src={lightbox} alt="büyük görünüm" style={{ maxWidth: "90vw", maxHeight: "90vh", borderRadius: 12, boxShadow: "0 20px 60px rgba(0,0,0,.5)" }} />
        </div>
      )}

      {/* Profil başlığı */}
      <div style={{ background: "var(--white)", border: "1px solid var(--border)", borderRadius: 18, padding: "1.75rem", marginBottom: "1.25rem", boxShadow: "var(--shadow)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
            {/* Profil fotoğrafı veya avatar */}
            {photos.length > 0 ? (
              <img src={photoUrl(photos[0].file_path)} alt={turtle.name}
                style={{ width: 72, height: 72, borderRadius: "50%", objectFit: "cover", border: `3px solid ${ac}`, boxShadow: `0 4px 14px ${ac}44`, flexShrink: 0, cursor: "pointer" }}
                onClick={() => setLightbox(photoUrl(photos[0].file_path))}
                onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
              />
            ) : (
              <div style={{ width: 72, height: 72, borderRadius: "50%", background: ac, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.9rem", fontWeight: 900, color: "#fff", boxShadow: `0 6px 20px ${ac}55`, flexShrink: 0 }}>
                {turtle.name.charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              {editing
                ? <input value={editName} onChange={(e) => setEditName(e.target.value)}
                    style={{ fontSize: "1.4rem", fontWeight: 900, width: "auto", border: "none", borderBottom: `2px solid ${ac}`, borderRadius: 0, padding: ".1rem 0", outline: "none", background: "transparent", color: "var(--ink)" }} />
                : <h1 style={{ fontSize: "1.5rem", fontWeight: 900, color: "var(--ink)", letterSpacing: "-.01em" }}>{turtle.name}</h1>
              }
              <div style={{ color: "var(--muted)", fontSize: ".82rem", marginTop: ".25rem", display: "flex", gap: ".75rem", flexWrap: "wrap" }}>
                <span>Kayıt: {new Date(turtle.registered_at).toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" })}</span>
                <span>·</span>
                <span style={{ color: "var(--teal)", fontWeight: 600 }}>{photos.length} fotoğraf</span>
                <span>·</span>
                <span style={{ color: "var(--teal)", fontWeight: 600 }}>{sightings.length} gözlem</span>
                {sonGozlem?.location_name && (
                  <><span>·</span><span>Son konum: <strong>{sonGozlem.location_name}</strong></span></>
                )}
              </div>
            </div>
          </div>
          <div style={{ display: "flex", gap: ".5rem", flexShrink: 0 }}>
            {editing
              ? <><button className="btn-primary" onClick={handleSave} disabled={saving}>{saving ? "…" : "Kaydet"}</button>
                  <button className="btn-ghost" onClick={() => setEditing(false)}>İptal</button></>
              : <><button className="btn-ghost" onClick={() => setEditing(true)}>Düzenle</button>
                  <button className="btn-danger" onClick={handleDelete}>Sil</button></>
            }
          </div>
        </div>

        {/* Notlar */}
        {editing ? (
          <div style={{ marginTop: "1rem" }}>
            <label>Notlar</label>
            <textarea rows={3} value={editNotes} onChange={(e) => setEditNotes(e.target.value)} placeholder="Gözlem notları, ayırt edici özellikler…" />
          </div>
        ) : turtle.notes ? (
          <div style={{ marginTop: "1rem", background: "linear-gradient(135deg,#f0fdfa,#e0f2fe)", border: "1px solid #99f6e4", borderRadius: 10, padding: ".9rem 1.1rem", color: "var(--ink-soft)", fontSize: ".92rem" }}>
            {turtle.notes}
          </div>
        ) : null}
      </div>

      {/* Harita */}
      <div style={{ background: "var(--white)", border: "1px solid var(--border)", borderRadius: 18, overflow: "hidden", marginBottom: "1.25rem", boxShadow: "var(--shadow)" }}>
        <div style={{ padding: "1rem 1.5rem", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontWeight: 700, fontSize: ".95rem" }}>Hareket Rotası</div>
          {sonGozlem?.location_name && (
            <span style={{ fontSize: ".82rem", color: "var(--muted)" }}>
              Son görüldüğü yer: <strong style={{ color: "var(--ink)" }}>{sonGozlem.location_name}</strong>
            </span>
          )}
        </div>
        <RouteMap geojson={geojson} />
        {!geojson && (
          <p style={{ padding: "1rem 1.5rem", color: "var(--muted)", fontSize: ".85rem" }}>
            Rota oluşturmak için en az 2 gözlem gereklidir.
          </p>
        )}
      </div>

      {/* Sekmeler */}
      <div style={{ display: "inline-flex", gap: ".25rem", marginBottom: "1.25rem", background: "var(--white)", border: "1px solid var(--border)", borderRadius: 10, padding: ".3rem" }}>
        {([
          { key: "gallery", label: `Galeri (${photos.length})` },
          { key: "photos",  label: "Fotoğraf Ekle" },
          { key: "sightings", label: "Gözlem Ekle" },
        ] as const).map(({ key, label }) => (
          <button key={key} onClick={() => setActiveTab(key)}
            style={{ padding: ".4rem 1.1rem", borderRadius: 7, fontWeight: 600, fontSize: ".88rem", border: "none", cursor: "pointer", transition: "all .15s",
              background: activeTab===key ? "linear-gradient(135deg,#0d9488,#0891b2)" : "transparent",
              color: activeTab===key ? "#fff" : "var(--muted)",
              boxShadow: activeTab===key ? "0 2px 8px rgba(13,148,136,.2)" : "none" }}>
            {label}
          </button>
        ))}
      </div>

      {/* Galeri sekmesi */}
      {activeTab === "gallery" && (
        <div className="card" style={{ borderRadius: 16 }}>
          {photos.length === 0 ? (
            <div style={{ textAlign: "center", padding: "3rem", color: "var(--muted)" }}>
              <div style={{ fontSize: "3rem", marginBottom: "1rem", opacity: .3 }}>📷</div>
              <p style={{ fontWeight: 600, marginBottom: ".4rem" }}>Henüz fotoğraf yok</p>
              <p style={{ fontSize: ".88rem" }}>
                <button className="btn-primary" style={{ marginTop: ".75rem" }} onClick={() => setActiveTab("photos")}>Fotoğraf Ekle</button>
              </p>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: "1rem" }}>
              {photos.map((p, i) => (
                <div key={p.id} style={{ position: "relative", borderRadius: 12, overflow: "hidden", aspectRatio: "1", cursor: "zoom-in", boxShadow: "var(--shadow)", border: "1px solid var(--border)" }}
                  onClick={() => setLightbox(photoUrl(p.file_path))}>
                  <img src={photoUrl(p.file_path)} alt={`fotoğraf ${i+1}`}
                    style={{ width: "100%", height: "100%", objectFit: "cover", transition: "transform .2s" }}
                    onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.04)")}
                    onMouseLeave={(e) => (e.currentTarget.style.transform = "")}
                    onError={(e) => { (e.currentTarget.parentElement!.style.background = "var(--bg)"); (e.currentTarget.style.display = "none"); }}
                  />
                  {i === 0 && (
                    <span style={{ position: "absolute", top: 6, left: 6, background: "var(--teal)", color: "#fff", fontSize: ".65rem", fontWeight: 700, padding: ".15rem .45rem", borderRadius: 99, letterSpacing: ".04em" }}>
                      ANA
                    </span>
                  )}
                  <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "linear-gradient(transparent,rgba(0,0,0,.55))", padding: ".4rem .6rem" }}>
                    <div style={{ fontSize: ".7rem", color: "rgba(255,255,255,.85)" }}>
                      {new Date(p.uploaded_at).toLocaleDateString("tr-TR")}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Fotoğraf yükleme sekmesi */}
      {activeTab === "photos" && (
        <div className="card" style={{ borderRadius: 16 }}>
          <div className="section-title">Yeni Fotoğraf Yükle</div>
          <DropZone onFile={setPhotoFile} />
          {photoFile && (
            <button className="btn-primary" style={{ marginTop: "1rem", width: "100%", borderRadius: 9 }}
              onClick={handlePhotoUpload} disabled={uploading}>
              {uploading ? "Yükleniyor…" : "Fotoğrafı Yükle"}
            </button>
          )}
          {uploadMsg && (
            <div style={{ marginTop: ".75rem", fontSize: ".88rem", padding: ".6rem 1rem", borderRadius: 8, background: uploadMsg.ok ? "#f0fdf4" : "#fef2f2", color: uploadMsg.ok ? "#15803d" : "var(--danger)" }}>
              {uploadMsg.text}
            </div>
          )}
        </div>
      )}

      {/* Gözlem sekmesi */}
      {activeTab === "sightings" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <div className="card" style={{ borderRadius: 16 }}>
            <div className="section-title">Yeni Gözlem Ekle</div>
            <div className="grid-2" style={{ gap: ".75rem", marginBottom: ".75rem" }}>
              <div><label>Enlem</label><input type="number" step="any" placeholder="36.5" value={lat} onChange={(e) => setLat(e.target.value)} /></div>
              <div><label>Boylam</label><input type="number" step="any" placeholder="28.0" value={lon} onChange={(e) => setLon(e.target.value)} /></div>
            </div>
            <label>Konum Adı (opsiyonel)</label>
            <input placeholder="Datça, Türkiye" value={locName} onChange={(e) => setLocName(e.target.value)} style={{ marginBottom: ".75rem" }} />
            <button className="btn-primary" style={{ width: "100%", borderRadius: 9 }}
              onClick={handleLogSighting} disabled={loggingSight || !lat || !lon}>
              {loggingSight ? "Kaydediliyor…" : "Gözlemi Kaydet"}
            </button>
            {sightMsg && (
              <div style={{ marginTop: ".75rem", fontSize: ".88rem", padding: ".6rem 1rem", borderRadius: 8, background: sightMsg.ok ? "#f0fdf4" : "#fef2f2", color: sightMsg.ok ? "#15803d" : "var(--danger)" }}>
                {sightMsg.text}
              </div>
            )}
          </div>

          {sightings.length > 0 && (
            <div className="card" style={{ borderRadius: 16 }}>
              <div className="section-title">Gözlem Geçmişi ({sightings.length})</div>
              <div style={{ display: "flex", flexDirection: "column", gap: ".5rem" }}>
                {[...sightings].reverse().map((s, i) => (
                  <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: ".7rem 1rem", borderRadius: 10, background: i===0 ? "linear-gradient(135deg,#f0fdfa,#e0f2fe)" : "var(--bg)" }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: ".9rem", color: "var(--ink)" }}>
                        {s.location_name ?? "Bilinmeyen konum"}
                      </div>
                      <div style={{ fontSize: ".75rem", color: "var(--muted)", marginTop: ".15rem" }}>
                        {s.latitude.toFixed(4)}°K, {s.longitude.toFixed(4)}°D
                      </div>
                    </div>
                    <div style={{ fontSize: ".78rem", color: "var(--muted)", fontWeight: 500 }}>
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
  );
}
