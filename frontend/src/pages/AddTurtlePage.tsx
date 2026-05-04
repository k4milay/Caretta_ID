import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DropZone from "../components/DropZone";
import { turtleApi, photoApi } from "../services/api";

type Step = "info" | "photo" | "done";

export default function AddTurtlePage() {
  const navigate = useNavigate();
  const [step, setStep]     = useState<Step>("info");
  const [name, setName]     = useState("");
  const [notes, setNotes]   = useState("");
  const [file, setFile]     = useState<File | null>(null);
  const [turtleId, setTurtleId] = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  async function handleCreateProfile() {
    if (!name.trim()) { setError("İsim zorunludur."); return; }
    setLoading(true);
    setError("");
    try {
      const t = await turtleApi.create(name.trim(), notes.trim() || undefined);
      setTurtleId(t.id);
      setStep("photo");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata oluştu.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUploadPhoto() {
    if (!turtleId) return;
    setLoading(true);
    setError("");
    try {
      if (file) await photoApi.upload(turtleId, file);
      setStep("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fotoğraf yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page" style={{ maxWidth: 520 }}>
      <h1 className="page-title">+ Yeni Kaplumbağa Kaydı</h1>

      {/* Step indicator */}
      <div style={{ display: "flex", gap: ".5rem", marginBottom: "1.5rem" }}>
        {(["info", "photo", "done"] as Step[]).map((s, i) => (
          <div key={s} style={{
            flex: 1, height: 4, borderRadius: 99,
            background: ["info","photo","done"].indexOf(step) >= i ? "var(--teal)" : "var(--border)",
            transition: "background .3s",
          }} />
        ))}
      </div>

      {error && <div className="card" style={{ color: "var(--danger)", marginBottom: "1rem" }}>❌ {error}</div>}

      {step === "info" && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label>İsim *</label>
            <input
              placeholder="Örn. Athena"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateProfile()}
            />
          </div>
          <div>
            <label>Notlar (opsiyonel)</label>
            <textarea rows={3} placeholder="Gözlem notları, özellikler…"
              value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <button className="btn-primary" onClick={handleCreateProfile} disabled={loading}>
            {loading ? "Oluşturuluyor…" : "Profil Oluştur →"}
          </button>
        </div>
      )}

      {step === "photo" && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ color: "var(--muted)", fontSize: ".9rem" }}>
            Tanımlama için en az bir baş/yüz fotoğrafı yükleyin. Daha sonra da ekleyebilirsiniz.
          </p>
          <DropZone onFile={setFile} />
          <div style={{ display: "flex", gap: ".75rem" }}>
            <button className="btn-outline" style={{ flex: 1 }} onClick={() => setStep("done")} disabled={loading}>
              Şimdi Atla
            </button>
            <button className="btn-primary" style={{ flex: 2 }} onClick={handleUploadPhoto} disabled={loading}>
              {loading ? "Yükleniyor…" : file ? "Fotoğrafı Yükle →" : "Fotoğraf seçin…"}
            </button>
          </div>
        </div>
      )}

      {step === "done" && turtleId && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem", textAlign: "center" }}>
          <div style={{ fontSize: "3rem" }}>🐢</div>
          <h2 style={{ fontSize: "1.2rem" }}>"{name}" başarıyla kaydedildi!</h2>
          <div style={{ display: "flex", gap: ".75rem" }}>
            <button className="btn-outline" style={{ flex: 1 }}
              onClick={() => navigate("/turtles")}>
              Tüm Kaplumbağalar
            </button>
            <button className="btn-primary" style={{ flex: 2 }}
              onClick={() => navigate(`/turtles/${turtleId}`)}>
              Profili Görüntüle →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
