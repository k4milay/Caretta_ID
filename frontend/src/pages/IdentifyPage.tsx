import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DropZone from "../components/DropZone";
import { identifyApi, type IdentificationResponse } from "../services/api";

type State = "idle" | "loading" | "found" | "notfound" | "error";

export default function IdentifyPage() {
  const navigate = useNavigate();
  const [file, setFile]         = useState<File | null>(null);
  const [state, setState]       = useState<State>("idle");
  const [result, setResult]     = useState<IdentificationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState("");

  async function handleQuery() {
    if (!file) return;
    setState("loading");
    setResult(null);
    try {
      const res = await identifyApi.identify(file, "head", 3);
      setResult(res);
      setState(res.accepted ? "found" : "notfound");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Bir hata oluştu.");
      setState("error");
    }
  }

  function handleReset() {
    setFile(null);
    setState("idle");
    setResult(null);
  }

  const topMatch = result?.matches?.[0];
  const pct = topMatch ? Math.round(topMatch.similarity_score * 100) : 0;

  return (
    <div style={{ minHeight: "calc(100vh - 62px)", background: "linear-gradient(160deg, #f0fdfa 0%, #f1f5f9 50%, #e0f2fe 100%)" }}>
      <div style={{ maxWidth: 580, margin: "0 auto", padding: "3rem 1.25rem" }}>

        {/* Hero */}
        <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          <div style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 72, height: 72, borderRadius: "50%", background: "linear-gradient(135deg,#0d9488,#0891b2)", boxShadow: "0 8px 24px rgba(13,148,136,.3)", marginBottom: "1.25rem", fontSize: "2rem" }}>
            🐢
          </div>
          <h1 style={{ fontSize: "2.1rem", fontWeight: 900, color: "var(--ink)", letterSpacing: "-.02em", marginBottom: ".5rem" }}>
            Kaplumbağa Tanımlama
          </h1>
          <p style={{ color: "var(--muted)", fontSize: "1rem", maxWidth: 400, margin: "0 auto" }}>
            Fotoğraf yükleyin — sistem anında benzerlik analizi yapsın.
          </p>
        </div>

        {/* Upload card */}
        <div className="card" style={{ boxShadow: "var(--shadow-lg)", borderRadius: 18, padding: "1.75rem" }}>
          <DropZone onFile={(f) => { setFile(f); setState("idle"); setResult(null); }} />

          {file && state === "idle" && (
            <button
              className="btn-primary fade-up"
              style={{ width: "100%", marginTop: "1rem", padding: ".8rem", fontSize: "1rem", borderRadius: 10 }}
              onClick={handleQuery}
            >
              Analiz Et
            </button>
          )}

          {state === "loading" && (
            <div style={{ textAlign: "center", padding: "1.25rem 0 .5rem" }}>
              <div style={{ width: 36, height: 36, border: "3px solid var(--teal-mid)", borderTopColor: "var(--teal)", borderRadius: "50%", animation: "spin .65s linear infinite", margin: "0 auto .75rem" }} />
              <p style={{ color: "var(--muted)", fontWeight: 500 }}>Görüntü analiz ediliyor…</p>
            </div>
          )}
        </div>

        {/* FOUND */}
        {state === "found" && topMatch && (
          <div className="card fade-up" style={{ marginTop: "1.25rem", boxShadow: "var(--shadow-md)", borderRadius: 18, padding: "1.75rem", border: "1.5px solid #99f6e4" }}>
            <div style={{ display: "flex", alignItems: "center", gap: ".6rem", marginBottom: "1.5rem" }}>
              <span style={{ fontSize: "1.5rem" }}>✅</span>
              <div>
                <div style={{ fontWeight: 700, color: "var(--ink)", fontSize: "1rem" }}>Kayıtlı kaplumbağa bulundu</div>
                <div style={{ fontSize: ".82rem", color: "var(--muted)" }}>Sistemde eşleşen bir kayıt var</div>
              </div>
            </div>

            {/* Main match */}
            <div style={{ background: "linear-gradient(135deg,#f0fdfa,#e0f2fe)", borderRadius: 12, padding: "1.25rem", marginBottom: "1rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
                <div>
                  <div style={{ fontSize: ".75rem", fontWeight: 700, color: "var(--teal)", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: ".3rem" }}>En yakın eşleşme</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 900, color: "var(--ink)", letterSpacing: "-.01em" }}>{topMatch.name}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "2.2rem", fontWeight: 900, color: "var(--teal)", lineHeight: 1 }}>{pct}%</div>
                  <div style={{ fontSize: ".75rem", color: "var(--muted)", marginTop: ".15rem" }}>benzerlik</div>
                </div>
              </div>

              {/* Progress bar */}
              <div style={{ height: 8, background: "rgba(255,255,255,.6)", borderRadius: 99, overflow: "hidden" }}>
                <div style={{ height: "100%", borderRadius: 99, width: `${pct}%`, transition: "width .7s ease", background: pct >= 80 ? "linear-gradient(90deg,#22c55e,#16a34a)" : pct >= 65 ? "linear-gradient(90deg,#f59e0b,#d97706)" : "linear-gradient(90deg,#f87171,#ef4444)" }} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: ".3rem", fontSize: ".72rem", color: "var(--muted)" }}>
                <span>0%</span><span>50%</span><span>100%</span>
              </div>
            </div>

            <button className="btn-primary" style={{ width: "100%", padding: ".75rem", borderRadius: 10, fontSize: ".95rem" }}
              onClick={() => navigate(`/turtles/${topMatch.turtle_id.toString()}`)}>
              Profilini Görüntüle →
            </button>

            {/* Other matches */}
            {result!.matches.length > 1 && (
              <>
                <hr className="divider" />
                <div className="section-title">Diğer olası eşleşmeler</div>
                {result!.matches.slice(1).map((m) => (
                  <div key={m.turtle_id.toString()}
                    onClick={() => navigate(`/turtles/${m.turtle_id.toString()}`)}
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: ".55rem .75rem", borderRadius: 8, cursor: "pointer", transition: "background .15s" }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                    <span style={{ fontWeight: 600, fontSize: ".9rem" }}>{m.name}</span>
                    <span style={{ fontSize: ".82rem", color: "var(--muted)", fontWeight: 600 }}>%{Math.round(m.similarity_score * 100)}</span>
                  </div>
                ))}
              </>
            )}

            <button className="btn-ghost" style={{ width: "100%", marginTop: "1rem" }} onClick={handleReset}>
              Yeni Sorgulama
            </button>
          </div>
        )}

        {/* NOT FOUND */}
        {state === "notfound" && (
          <div className="card fade-up" style={{ marginTop: "1.25rem", boxShadow: "var(--shadow-md)", borderRadius: 18, padding: "2rem", textAlign: "center", border: "1.5px solid #fecaca" }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔍</div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 800, color: "var(--ink)", marginBottom: ".5rem" }}>
              Kayıt bulunamadı
            </h2>
            <p style={{ color: "var(--muted)", fontSize: ".9rem", marginBottom: "1.75rem", maxWidth: 320, margin: "0 auto 1.75rem" }}>
              Bu kaplumbağa sistemde kayıtlı değil. Yeni bir profil oluşturarak veritabanına ekleyebilirsiniz.
            </p>
            <div style={{ display: "flex", gap: ".75rem", justifyContent: "center" }}>
              <button className="btn-ghost" onClick={handleReset}>Tekrar Dene</button>
              <button className="btn-primary" style={{ padding: ".65rem 1.5rem" }} onClick={() => navigate("/turtles/new")}>
                Yeni Kayıt Oluştur
              </button>
            </div>
          </div>
        )}

        {/* ERROR */}
        {state === "error" && (
          <div className="card fade-up" style={{ marginTop: "1.25rem", borderRadius: 18, border: "1.5px solid #fecaca" }}>
            <div style={{ color: "var(--danger)", fontWeight: 600, marginBottom: ".5rem" }}>Hata oluştu</div>
            <div style={{ color: "var(--muted)", fontSize: ".85rem", marginBottom: "1rem" }}>{errorMsg}</div>
            <button className="btn-ghost" onClick={handleReset}>Tekrar Dene</button>
          </div>
        )}
      </div>
    </div>
  );
}
