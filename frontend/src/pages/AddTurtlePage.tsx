import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DropZone from "../components/DropZone";
import { turtleApi, photoApi } from "../services/api";

type Step = "info" | "photo" | "done";

const STEPS = [
  { key: "info",  label: "Bilgi",     icon: "📋" },
  { key: "photo", label: "Fotoğraf",  icon: "📷" },
  { key: "done",  label: "Tamamlandı",icon: "✅" },
] as const;

export default function AddTurtlePage() {
  const navigate = useNavigate();
  const [step, setStep]         = useState<Step>("info");
  const [name, setName]         = useState("");
  const [notes, setNotes]       = useState("");
  const [file, setFile]         = useState<File | null>(null);
  const [turtleId, setTurtleId] = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  const stepIdx = STEPS.findIndex(s => s.key === step);

  async function handleCreateProfile() {
    if (!name.trim()) { setError("İsim zorunludur."); return; }
    setLoading(true); setError("");
    try {
      const t = await turtleApi.create(name.trim(), notes.trim() || undefined);
      setTurtleId(t.id);
      setStep("photo");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Hata oluştu.");
    } finally { setLoading(false); }
  }

  async function handleUploadPhoto() {
    if (!turtleId) return;
    setLoading(true); setError("");
    try {
      if (file) await photoApi.upload(turtleId, file);
      setStep("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fotoğraf yüklenemedi.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      {/* ── Header banner ── */}
      <div style={{
        background: "linear-gradient(135deg, #0a2540 0%, #0c4a6e 60%, #0d9488 100%)",
        padding: "3rem 2rem 5rem",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{ position: "absolute", width: 300, height: 300, borderRadius: "50%", background: "rgba(255,255,255,.03)", top: -80, right: -60, pointerEvents: "none" }} />
        <div style={{ maxWidth: 560, margin: "0 auto" }}>
          <p style={{ fontSize: ".72rem", fontWeight: 800, color: "rgba(153,246,228,.85)", textTransform: "uppercase", letterSpacing: ".12em", marginBottom: ".5rem" }}>Yeni Kayıt</p>
          <h1 style={{ fontSize: "2rem", fontWeight: 900, color: "#fff", letterSpacing: "-.03em" }}>Kaplumbağa Profili Oluştur</h1>
          <p style={{ color: "rgba(255,255,255,.6)", fontSize: ".9rem", marginTop: ".4rem" }}>Bilgileri doldurun ve referans fotoğraf ekleyin.</p>
        </div>
      </div>

      <div style={{ maxWidth: 560, margin: "-3.5rem auto 0", padding: "0 1.25rem 5rem", position: "relative", zIndex: 10 }}>

        {/* ── Step indicator ── */}
        <div style={{ background: "#fff", borderRadius: 20, padding: "1.25rem 1.5rem", marginBottom: "1.25rem", boxShadow: "0 20px 60px rgba(12,74,110,.15)", border: "1px solid rgba(255,255,255,.9)" }}>
          <div style={{ display: "flex", gap: ".5rem", alignItems: "center" }}>
            {STEPS.map((s, i) => {
              const active = i === stepIdx;
              const done   = i < stepIdx;
              return (
                <div key={s.key} style={{ flex: 1, display: "flex", flexDirection: "column", gap: ".4rem" }}>
                  <div style={{ height: 4, borderRadius: 99, background: done ? "#0d9488" : active ? "linear-gradient(90deg,#0d9488,#0891b2)" : "#e2e8f0", transition: "background .3s" }} />
                  <div style={{ display: "flex", alignItems: "center", gap: ".3rem" }}>
                    <span style={{ fontSize: ".8rem" }}>{done ? "✓" : s.icon}</span>
                    <span style={{ fontSize: ".72rem", fontWeight: 700, color: done || active ? "#0d9488" : "#94a3b8", textTransform: "uppercase", letterSpacing: ".04em" }}>{s.label}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Error ── */}
        {error && (
          <div style={{ color: "var(--danger)", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, padding: ".75rem 1rem", marginBottom: "1rem", fontSize: ".88rem", fontWeight: 500 }}>
            {error}
          </div>
        )}

        {/* ── Step: Info ── */}
        {step === "info" && (
          <div className="scale-in" style={{ background: "#fff", borderRadius: 22, padding: "1.75rem", boxShadow: "0 16px 48px rgba(12,74,110,.12)", border: "1px solid rgba(255,255,255,.9)" }}>
            <div style={{ marginBottom: "1.25rem" }}>
              <div style={{ fontSize: "1.5rem", marginBottom: ".5rem" }}>📋</div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 800, color: "#0f172a" }}>Temel Bilgiler</h2>
              <p style={{ color: "#64748b", fontSize: ".85rem", marginTop: ".2rem" }}>Kaplumbağa adı ve gözlem notlarını girin.</p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "1.1rem" }}>
              <div>
                <label>İsim *</label>
                <input placeholder="Örn. Athena" value={name} onChange={e => setName(e.target.value)} onKeyDown={e => e.key === "Enter" && handleCreateProfile()} autoFocus />
              </div>
              <div>
                <label>Notlar (opsiyonel)</label>
                <textarea rows={3} placeholder="Gözlem notları, ayırt edici özellikler…" value={notes} onChange={e => setNotes(e.target.value)} />
              </div>
              <button className="btn-primary" style={{ padding: ".8rem", borderRadius: 12, fontSize: ".95rem" }} onClick={handleCreateProfile} disabled={loading || !name.trim()}>
                {loading ? "Oluşturuluyor…" : "Devam Et →"}
              </button>
            </div>
          </div>
        )}

        {/* ── Step: Photo ── */}
        {step === "photo" && (
          <div className="scale-in" style={{ background: "#fff", borderRadius: 22, padding: "1.75rem", boxShadow: "0 16px 48px rgba(12,74,110,.12)", border: "1px solid rgba(255,255,255,.9)" }}>
            <div style={{ marginBottom: "1.25rem" }}>
              <div style={{ fontSize: "1.5rem", marginBottom: ".5rem" }}>📷</div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 800, color: "#0f172a" }}>Referans Fotoğraf</h2>
              <p style={{ color: "#64748b", fontSize: ".85rem", marginTop: ".2rem" }}>Tanımlama için tam vücut fotoğrafı yükleyin. Daha sonra da ekleyebilirsiniz.</p>
            </div>
            <DropZone onFile={setFile} />
            <div style={{ display: "flex", gap: ".75rem", marginTop: "1.25rem" }}>
              <button className="btn-ghost" style={{ flex: 1, borderRadius: 11 }} onClick={() => setStep("done")} disabled={loading}>
                Şimdi Atla
              </button>
              <button className="btn-primary" style={{ flex: 2, borderRadius: 11 }} onClick={handleUploadPhoto} disabled={loading || !file}>
                {loading ? "Yükleniyor…" : "Fotoğrafı Yükle"}
              </button>
            </div>
          </div>
        )}

        {/* ── Step: Done ── */}
        {step === "done" && turtleId && (
          <div className="scale-in" style={{ background: "#fff", borderRadius: 22, padding: "2.5rem 2rem", boxShadow: "0 16px 48px rgba(12,74,110,.12)", border: "1px solid rgba(255,255,255,.9)", textAlign: "center" }}>
            <div style={{
              width: 80, height: 80, borderRadius: "50%",
              background: "linear-gradient(135deg,#f0fdfa,#d1fae5)",
              border: "3px solid #6ee7b7",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "2rem", margin: "0 auto 1.25rem",
              boxShadow: "0 8px 24px rgba(16,185,129,.2)",
            }}>
              ✅
            </div>
            <h2 style={{ fontSize: "1.35rem", fontWeight: 900, color: "#0f172a", marginBottom: ".4rem", letterSpacing: "-.02em" }}>
              "{name}" kaydedildi!
            </h2>
            <p style={{ color: "#64748b", fontSize: ".9rem", marginBottom: "2rem" }}>Profil başarıyla oluşturuldu. Fotoğraf ekleyebilir veya gözlem girebilirsiniz.</p>
            <div style={{ display: "flex", gap: ".75rem" }}>
              <button className="btn-ghost" style={{ flex: 1, borderRadius: 11 }} onClick={() => navigate("/turtles")}>
                Tüm Liste
              </button>
              <button className="btn-primary" style={{ flex: 2, borderRadius: 11 }} onClick={() => navigate(`/turtles/${turtleId}`)}>
                Profilini Gör →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
