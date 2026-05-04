import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import RouteMap from "../components/RouteMap";
import DropZone from "../components/DropZone";
import {
  turtleApi, photoApi, sightingApi,
  type Turtle, type Sighting, type GeoJSON,
} from "../services/api";

export default function TurtleProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [turtle,   setTurtle]   = useState<Turtle | null>(null);
  const [sightings,setSightings]= useState<Sighting[]>([]);
  const [geojson,  setGeojson]  = useState<GeoJSON | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");

  // Photo upload state
  const [photoFile,    setPhotoFile]    = useState<File | null>(null);
  const [uploading,    setUploading]    = useState(false);
  const [uploadMsg,    setUploadMsg]    = useState("");

  // Sighting form state
  const [lat,          setLat]          = useState("");
  const [lon,          setLon]          = useState("");
  const [locName,      setLocName]      = useState("");
  const [loggingSight, setLoggingSight] = useState(false);
  const [sightMsg,     setSightMsg]     = useState("");

  // Edit state
  const [editing,  setEditing]  = useState(false);
  const [editName, setEditName] = useState("");
  const [editNotes,setEditNotes]= useState("");

  useEffect(() => { if (id) load(); }, [id]);

  async function load() {
    setLoading(true);
    try {
      const [t, s, g] = await Promise.all([
        turtleApi.get(id!),
        sightingApi.list(id!),
        sightingApi.route(id!).catch(() => null),
      ]);
      setTurtle(t);
      setEditName(t.name);
      setEditNotes(t.notes ?? "");
      setSightings(s);
      setGeojson(g);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  }

  async function handlePhotoUpload() {
    if (!photoFile || !id) return;
    setUploading(true);
    setUploadMsg("");
    try {
      await photoApi.upload(id, photoFile);
      setUploadMsg("✅ Fotoğraf yüklendi ve gömme vektörü güncellendi.");
      setPhotoFile(null);
    } catch (e) {
      setUploadMsg("❌ " + (e instanceof Error ? e.message : "Hata"));
    } finally {
      setUploading(false);
    }
  }

  async function handleLogSighting() {
    if (!id || !lat || !lon) return;
    setLoggingSight(true);
    setSightMsg("");
    try {
      const s = await sightingApi.log(id, {
        latitude: parseFloat(lat),
        longitude: parseFloat(lon),
        location_name: locName || undefined,
      });
      setSightings((prev) => [...prev, s]);
      setGeojson(await sightingApi.route(id));
      setLat(""); setLon(""); setLocName("");
      setSightMsg("✅ Gözlem kaydedildi.");
    } catch (e) {
      setSightMsg("❌ " + (e instanceof Error ? e.message : "Hata"));
    } finally {
      setLoggingSight(false);
    }
  }

  async function handleSave() {
    if (!id) return;
    const updated = await turtleApi.update(id, { name: editName, notes: editNotes });
    setTurtle(updated);
    setEditing(false);
  }

  async function handleDelete() {
    if (!id || !confirm(`"${turtle?.name}" silinsin mi? Bu işlem geri alınamaz.`)) return;
    await turtleApi.delete(id);
    navigate("/turtles");
  }

  if (loading) return <div className="page empty">Yükleniyor…</div>;
  if (error)   return <div className="page"><div className="card" style={{ color: "var(--danger)" }}>❌ {error}</div></div>;
  if (!turtle) return null;

  return (
    <div className="page">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
        <div>
          {editing
            ? <input value={editName} onChange={(e) => setEditName(e.target.value)}
                style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: ".5rem" }} />
            : <h1 className="page-title" style={{ marginBottom: ".25rem" }}>🐢 {turtle.name}</h1>
          }
          <div style={{ color: "var(--muted)", fontSize: ".85rem" }}>
            Kayıt: {new Date(turtle.registered_at).toLocaleDateString("tr-TR")}
          </div>
        </div>
        <div style={{ display: "flex", gap: ".5rem" }}>
          {editing
            ? <><button className="btn-primary" onClick={handleSave}>Kaydet</button>
                <button className="btn-outline" onClick={() => setEditing(false)}>İptal</button></>
            : <><button className="btn-outline" onClick={() => setEditing(true)}>Düzenle</button>
                <button className="btn-danger" onClick={handleDelete}>Sil</button></>
          }
        </div>
      </div>

      {editing && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <label>Notlar</label>
          <textarea rows={3} value={editNotes} onChange={(e) => setEditNotes(e.target.value)} />
        </div>
      )}
      {!editing && turtle.notes && (
        <div className="card" style={{ marginBottom: "1rem", color: "var(--muted)", fontStyle: "italic" }}>
          {turtle.notes}
        </div>
      )}

      <div className="grid-2" style={{ gap: "1.5rem" }}>
        {/* Left column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {/* Photo upload */}
          <div className="card">
            <h2 style={{ marginBottom: ".75rem", fontSize: "1rem" }}>📷 Fotoğraf Ekle</h2>
            <DropZone onFile={setPhotoFile} />
            {photoFile && (
              <button className="btn-primary" style={{ marginTop: ".75rem", width: "100%" }}
                onClick={handlePhotoUpload} disabled={uploading}>
                {uploading ? "Yükleniyor…" : "Yükle ve Gömme Vektörünü Güncelle"}
              </button>
            )}
            {uploadMsg && <p style={{ marginTop: ".5rem", fontSize: ".85rem" }}>{uploadMsg}</p>}
          </div>

          {/* Log sighting */}
          <div className="card">
            <h2 style={{ marginBottom: ".75rem", fontSize: "1rem" }}>📍 Gözlem Ekle</h2>
            <div style={{ display: "flex", gap: ".5rem", marginBottom: ".5rem" }}>
              <div style={{ flex: 1 }}>
                <label>Enlem</label>
                <input type="number" step="any" placeholder="36.5" value={lat} onChange={(e) => setLat(e.target.value)} />
              </div>
              <div style={{ flex: 1 }}>
                <label>Boylam</label>
                <input type="number" step="any" placeholder="28.0" value={lon} onChange={(e) => setLon(e.target.value)} />
              </div>
            </div>
            <label>Konum Adı (opsiyonel)</label>
            <input placeholder="Datça, Türkiye" value={locName} onChange={(e) => setLocName(e.target.value)}
              style={{ marginBottom: ".5rem" }} />
            <button className="btn-primary" style={{ width: "100%" }}
              onClick={handleLogSighting} disabled={loggingSight || !lat || !lon}>
              {loggingSight ? "Kaydediliyor…" : "Gözlemi Kaydet"}
            </button>
            {sightMsg && <p style={{ marginTop: ".5rem", fontSize: ".85rem" }}>{sightMsg}</p>}
          </div>

          {/* Sightings list */}
          <div className="card">
            <h2 style={{ marginBottom: ".75rem", fontSize: "1rem" }}>📋 Gözlem Geçmişi ({sightings.length})</h2>
            {sightings.length === 0
              ? <p style={{ color: "var(--muted)", fontSize: ".85rem" }}>Henüz gözlem kaydı yok.</p>
              : <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: ".5rem" }}>
                  {sightings.map((s) => (
                    <li key={s.id} style={{ fontSize: ".85rem", borderBottom: "1px solid var(--border)", paddingBottom: ".4rem" }}>
                      <b>{s.location_name ?? "Bilinmeyen konum"}</b>
                      <br />
                      {s.latitude.toFixed(4)}, {s.longitude.toFixed(4)} —&nbsp;
                      {new Date(s.sighted_at).toLocaleDateString("tr-TR")}
                    </li>
                  ))}
                </ul>
            }
          </div>
        </div>

        {/* Right column — map */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "1rem", borderBottom: "1px solid var(--border)" }}>
            <h2 style={{ fontSize: "1rem" }}>🗺️ Hareket Rotası</h2>
          </div>
          <RouteMap geojson={geojson} />
          {!geojson && (
            <p style={{ padding: "1rem", color: "var(--muted)", fontSize: ".85rem" }}>
              Rota için en az 2 gözlem gereklidir.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
