import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DropZone from "../components/DropZone";
import { turtleApi, photoApi } from "../services/api";

type Step = "info" | "photo" | "done";

export default function AddTurtlePage() {
  const navigate = useNavigate();
  const [step, setStep]         = useState<Step>("info");
  const [name, setName]         = useState("");
  const [notes, setNotes]       = useState("");
  const [file, setFile]         = useState<File | null>(null);
  const [turtleId, setTurtleId] = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  const steps: Step[] = ["info", "photo", "done"];
  const stepIdx = steps.indexOf(step);

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
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "1.6rem", fontWeight: 800, color: "var(--ink)", marginBottom: ".35rem" }}>
          Yeni Kaplumbağa Kaydı
        </h1>
        <p style={{ color: "var(--muted)", fontSize: ".9rem" }}>
          Bilgileri doldurun ve fotoğraf ekleyin.
        </p>
      </div>

      {/* Step bar */}
      <div style={{ display: "flex", gap: ".5rem", marginBottom: "1.75rem", alignItems: "center" }}>
        {steps.map((s, i) => (
          <div key={s} style={{ flex: 1, display: "flex", flexDirection: "column", gap: ".3rem" }}>
            <div style={{ height: 4, borderRadius: 99, background: stepIdx >= i ? "var(--teal)" : "var(--border)", transition: "background .3s" }} />
            <div style={{ fontSize: ".72rem", color: stepIdx >= i ? "var(--teal)" : "var(--muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".04em" }}>
              {s === "info" ? "Bilgi" : s === "photo" ? "Fotoğraf" : "Tamamlandı"}
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div style={{ color: "var(--danger)", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "var(--radius-sm)", padding: ".6rem .9rem", marginBottom: "1rem", fontSize: ".88rem" }}>
          {error}
        </div>
      )}

      {step === "info" && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label>İsim *</label>
            <input
              placeholder="Örn. Athena"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateProfile()}
              autoFocus
            />
          </div>
          <div>
            <label>Notlar (opsiyonel)</label>
            <textarea rows={3} placeholder="Gözlem notları, ayırt edici özellikler…"
              value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <button className="btn-primary" style={{ padding: ".7rem" }} onClick={handleCreateProfile} disabled={loading || !name.trim()}>
            {loading ? "Oluşturuluyor…" : "Devam Et"}
          </button>
        </div>
      )}

      {step === "photo" && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <p style={{ color: "var(--muted)", fontSize: ".9rem" }}>
            Tanımlama için baş/yüz fotoğrafı yükleyin. Daha sonra da ekleyebilirsiniz.
          </p>
          <DropZone onFile={setFile} />
          <div style={{ display: "flex", gap: ".75rem" }}>
            <button className="btn-ghost" style={{ flex: 1 }} onClick={() => setStep("done")} disabled={loading}>
              Şimdi Atla
            </button>
            <button className="btn-primary" style={{ flex: 2 }} onClick={handleUploadPhoto} disabled={loading || !file}>
              {loading ? "Yükleniyor…" : "Fotoğrafı Yükle"}
            </button>
          </div>
        </div>
      )}

      {step === "done" && turtleId && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem", textAlign: "center", padding: "2rem" }}>
          <div style={{ width: 64, height: 64, borderRadius: "50%", background: "var(--teal-lt)", color: "var(--teal)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.6rem", fontWeight: 800, margin: "0 auto" }}>
            {name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: ".35rem" }}>"{name}" kaydedildi!</h2>
            <p style={{ color: "var(--muted)", fontSize: ".9rem" }}>Profil başarıyla oluşturuldu.</p>
          </div>
          <div style={{ display: "flex", gap: ".75rem" }}>
            <button className="btn-ghost" style={{ flex: 1 }} onClick={() => navigate("/turtles")}>
              Tüm Listesi
            </button>
            <button className="btn-primary" style={{ flex: 2 }} onClick={() => navigate(`/turtles/${turtleId}`)}>
              Profili Gör
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
