import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DropZone from "../components/DropZone";
import { identifyApi, type IdentificationResponse, type MatchResult } from "../services/api";

type State = "idle" | "loading" | "found" | "candidates" | "notfound" | "noturtle" | "error";

const CONF_LABELS: Record<string, string> = {
  high:   "Yüksek güven",
  medium: "Orta güven",
  low:    "Düşük güven",
};

function ScoreBar({ score, color }: { score: number; color: string }) {
  return (
    <div style={{ height: 7, background: "#f1f5f9", borderRadius: 99, overflow: "hidden" }}>
      <div style={{
        height: "100%", borderRadius: 99,
        width: `${Math.round(score * 100)}%`,
        background: `linear-gradient(90deg, ${color}88, ${color})`,
        transition: "width .8s cubic-bezier(.4,0,.2,1)",
        boxShadow: `0 0 8px ${color}44`,
      }} />
    </div>
  );
}

function MatchRow({ m, onClick }: { m: MatchResult; onClick: () => void }) {
  const pct = Math.round(m.similarity_score * 100);
  const color = pct >= 76 ? "#10b981" : pct >= 73 ? "#f59e0b" : "#f97316";
  return (
    <div onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: ".9rem",
      padding: ".75rem 1rem", borderRadius: 13, cursor: "pointer",
      border: "1.5px solid #f1f5f9", background: "#fafcff",
      transition: "all .16s cubic-bezier(.4,0,.2,1)",
    }}
    onMouseEnter={e => { e.currentTarget.style.background = "#fff"; e.currentTarget.style.borderColor = `${color}44`; e.currentTarget.style.boxShadow = `0 4px 16px ${color}18`; e.currentTarget.style.transform = "translateY(-1px)"; }}
    onMouseLeave={e => { e.currentTarget.style.background = "#fafcff"; e.currentTarget.style.borderColor = "#f1f5f9"; e.currentTarget.style.boxShadow = "none"; e.currentTarget.style.transform = ""; }}>
      <div style={{
        width: 40, height: 40, borderRadius: "50%", flexShrink: 0,
        background: `linear-gradient(135deg, ${color}, ${color}cc)`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "1rem", fontWeight: 900, color: "#fff",
        boxShadow: `0 3px 10px ${color}40`,
      }}>
        {m.name.charAt(0).toUpperCase()}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: ".9rem", color: "#0f172a", marginBottom: ".3rem" }}>{m.name}</div>
        <ScoreBar score={m.similarity_score} color={color} />
      </div>
      <div style={{ textAlign: "right", flexShrink: 0 }}>
        <div style={{ fontSize: "1.2rem", fontWeight: 900, color, letterSpacing: "-.01em" }}>{pct}%</div>
        <div style={{ fontSize: ".6rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".05em", color, background: `${color}15`, padding: ".1rem .45rem", borderRadius: 99 }}>
          {CONF_LABELS[m.confidence] ?? m.confidence}
        </div>
      </div>
    </div>
  );
}

/* ── Stat chip ──────────────────────────────────────────────────────── */
function StatChip({ icon, label }: { icon: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: ".4rem", background: "rgba(255,255,255,.12)", backdropFilter: "blur(8px)", borderRadius: 99, padding: ".35rem .85rem", border: "1px solid rgba(255,255,255,.2)" }}>
      <span style={{ fontSize: ".95rem" }}>{icon}</span>
      <span style={{ fontSize: ".8rem", fontWeight: 600, color: "rgba(255,255,255,.9)" }}>{label}</span>
    </div>
  );
}

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
      const res = await identifyApi.identify(file, "body", 5);
      setResult(res);
      if (!res.turtle_detected)                          setState("noturtle");
      else if (res.accepted)                             setState("found");
      else if (res.candidates && res.candidates.length > 0) setState("candidates");
      else                                               setState("notfound");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Bir hata oluştu.");
      setState("error");
    }
  }

  function handleReset() { setFile(null); setState("idle"); setResult(null); }

  const top     = result?.matches?.[0];
  const topPct  = top ? Math.round(top.similarity_score * 100) : 0;
  const barColor = topPct >= 76 ? "#10b981" : topPct >= 73 ? "#f59e0b" : "#f97316";
  const showNewRegister = !result?.accepted || topPct < 76;

  return (
    <div style={{ minHeight: "calc(100vh - 64px)" }}>

      {/* ══════════════════════════════════════════ HERO ═══ */}
      <div style={{
        background: "linear-gradient(145deg, #0a2540 0%, #0c4a6e 35%, #0d9488 75%, #10b981 100%)",
        padding: "5rem 1.5rem 8rem",
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Decorative circles */}
        <div style={{ position: "absolute", width: 600, height: 600, borderRadius: "50%", background: "rgba(255,255,255,.025)", top: -200, right: -150, pointerEvents: "none" }} />
        <div style={{ position: "absolute", width: 300, height: 300, borderRadius: "50%", background: "rgba(255,255,255,.04)", bottom: -100, left: -50, pointerEvents: "none" }} />

        <div style={{ maxWidth: 700, margin: "0 auto", textAlign: "center", position: "relative" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            width: 88, height: 88, borderRadius: "50%",
            background: "rgba(255,255,255,.12)",
            backdropFilter: "blur(12px)",
            border: "2px solid rgba(255,255,255,.22)",
            boxShadow: "0 12px 40px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.18)",
            marginBottom: "1.5rem",
            fontSize: "2.4rem",
          }}>🐢</div>

          <h1 style={{
            fontSize: "clamp(2rem,5vw,3.2rem)", fontWeight: 900,
            color: "#fff", letterSpacing: "-.04em",
            lineHeight: 1.1, marginBottom: "1rem",
            textShadow: "0 2px 24px rgba(0,0,0,.25)",
          }}>
            Kaplumbağa Tanımlama
          </h1>

          <p style={{ color: "rgba(255,255,255,.75)", fontSize: "1.05rem", lineHeight: 1.7, maxWidth: 440, margin: "0 auto 2rem" }}>
            Caretta caretta bireylerini fotoğraftan yapay zekayla tanıyın.
            Sistem anında benzerlik analizi yaparak veritabanıyla eşleştirir.
          </p>

          <div style={{ display: "flex", justifyContent: "center", gap: ".75rem", flexWrap: "wrap" }}>
            <StatChip icon="🔬" label="AI Destekli Analiz" />
            <StatChip icon="⚡" label="Saniyeler İçinde Sonuç" />
            <StatChip icon="🧬" label="1024-D Embedding" />
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════ CARD ═══ */}
      <div style={{ maxWidth: 620, margin: "-4rem auto 0", padding: "0 1.25rem 5rem", position: "relative", zIndex: 10 }}>

        {/* Upload card */}
        <div style={{
          background: "#fff",
          borderRadius: 28,
          padding: "2rem",
          boxShadow: "0 30px 80px rgba(12,74,110,.2), 0 6px 20px rgba(0,0,0,.08)",
          border: "1px solid rgba(255,255,255,.9)",
        }}>
          <div style={{ marginBottom: "1.25rem" }}>
            <p style={{ fontSize: ".72rem", fontWeight: 800, color: "#0d9488", textTransform: "uppercase", letterSpacing: ".1em", marginBottom: ".3rem" }}>Analiz Başlat</p>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", letterSpacing: "-.02em" }}>Fotoğraf Yükle</h2>
          </div>

          <DropZone onFile={(f) => { setFile(f); setState("idle"); setResult(null); }} />

          {file && state === "idle" && (
            <button className="btn-primary fade-up"
              style={{ width: "100%", marginTop: "1.1rem", padding: ".95rem", fontSize: "1rem", borderRadius: 14, letterSpacing: ".01em" }}
              onClick={handleQuery}>
              Analiz Et →
            </button>
          )}

          {state === "loading" && (
            <div style={{ textAlign: "center", padding: "2rem 0 .5rem" }}>
              <div className="spinner" style={{ margin: "0 auto 1rem", width: 40, height: 40 }} />
              <p style={{ color: "#64748b", fontWeight: 600, fontSize: ".9rem" }}>Görüntü analiz ediliyor…</p>
              <p style={{ color: "#94a3b8", fontSize: ".8rem", marginTop: ".25rem" }}>Bu işlem birkaç saniye sürebilir</p>
            </div>
          )}
        </div>

        {/* ── FOUND ── */}
        {state === "found" && top && (
          <div className="fade-up" style={{ marginTop: "1.5rem", borderRadius: 24, background: "#fff", boxShadow: "0 20px 60px rgba(12,74,110,.15)", overflow: "hidden", border: "1px solid rgba(255,255,255,.9)" }}>
            <div style={{ background: "linear-gradient(135deg, #0d9488, #0891b2)", padding: "1.2rem 1.75rem", display: "flex", alignItems: "center", gap: ".85rem" }}>
              <div style={{ width: 42, height: 42, borderRadius: "50%", background: "rgba(255,255,255,.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.3rem", flexShrink: 0 }}>✅</div>
              <div>
                <div style={{ fontWeight: 800, color: "#fff", fontSize: "1rem" }}>Kayıtlı kaplumbağa bulundu!</div>
                <div style={{ fontSize: ".8rem", color: "rgba(255,255,255,.72)" }}>Sistemde eşleşen bir kayıt mevcut</div>
              </div>
            </div>

            <div style={{ padding: "1.75rem" }}>
              {/* Ana eşleşme */}
              <div style={{ display: "flex", alignItems: "center", gap: "1.1rem", marginBottom: "1.25rem", padding: "1.1rem", background: "linear-gradient(135deg,#f0fdfa,#e0f2fe)", borderRadius: 16, border: `1.5px solid ${barColor}22` }}>
                <div style={{ width: 60, height: 60, borderRadius: "50%", flexShrink: 0, background: `linear-gradient(135deg, ${barColor}, ${barColor}cc)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.5rem", fontWeight: 900, color: "#fff", boxShadow: `0 6px 18px ${barColor}44` }}>
                  {top.name.charAt(0).toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: ".7rem", fontWeight: 800, color: "#0d9488", textTransform: "uppercase", letterSpacing: ".08em" }}>En yakın eşleşme</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 900, color: "#0f172a", letterSpacing: "-.02em", lineHeight: 1.15 }}>{top.name}</div>
                  <div style={{ marginTop: ".5rem" }}><ScoreBar score={top.similarity_score} color={barColor} /></div>
                </div>
                <div style={{ textAlign: "right", flexShrink: 0 }}>
                  <div style={{ fontSize: "2.6rem", fontWeight: 900, color: barColor, lineHeight: 1, letterSpacing: "-.02em" }}>{topPct}%</div>
                  <div style={{ fontSize: ".65rem", fontWeight: 800, letterSpacing: ".05em", textTransform: "uppercase", color: barColor, background: `${barColor}15`, padding: ".15rem .5rem", borderRadius: 99, marginTop: ".2rem", display: "inline-block" }}>
                    {CONF_LABELS[top.confidence] ?? top.confidence}
                  </div>
                </div>
              </div>

              <button className="btn-primary"
                style={{ width: "100%", padding: ".85rem", borderRadius: 13, fontSize: ".95rem", marginBottom: ".75rem" }}
                onClick={() => navigate(`/turtles/${top.turtle_id.toString()}`)}>
                Profilini Görüntüle →
              </button>

              {result!.matches.length > 1 && (
                <>
                  <hr className="divider" />
                  <div className="section-label">Diğer eşleşmeler</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: ".45rem" }}>
                    {result!.matches.slice(1).map(m => (
                      <MatchRow key={m.turtle_id.toString()} m={m} onClick={() => navigate(`/turtles/${m.turtle_id.toString()}`)} />
                    ))}
                  </div>
                </>
              )}

              {result!.candidates?.length > 0 && (
                <>
                  <hr className="divider" />
                  <div style={{ display: "flex", alignItems: "center", gap: ".5rem", marginBottom: ".6rem" }}>
                    <div className="section-label" style={{ margin: 0 }}>Düşük benzerlikli adaylar</div>
                    <span style={{ fontSize: ".68rem", color: "#94a3b8", background: "#f8fafc", padding: ".12rem .5rem", borderRadius: 99, border: "1px solid #e2e8f0" }}>eşik altı</span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: ".45rem" }}>
                    {result!.candidates.map(m => (
                      <MatchRow key={m.turtle_id.toString()} m={m} onClick={() => navigate(`/turtles/${m.turtle_id.toString()}`)} />
                    ))}
                  </div>
                </>
              )}

              {showNewRegister && (
                <>
                  <hr className="divider" />
                  <div style={{ background: "#fffbeb", border: "1.5px solid #fde68a", borderRadius: 13, padding: "1rem 1.1rem", marginBottom: ".85rem" }}>
                    <div style={{ fontWeight: 800, fontSize: ".85rem", color: "#92400e", marginBottom: ".2rem" }}>Yeni bir kaplumbağa mı?</div>
                    <div style={{ fontSize: ".8rem", color: "#78350f" }}>Eşleşme güven eşiğinin altında. Yeni profil oluşturabilirsiniz.</div>
                  </div>
                  <button className="btn-primary" style={{ width: "100%", borderRadius: 11, background: "linear-gradient(135deg,#d97706,#b45309)", marginBottom: ".6rem" }}
                    onClick={() => navigate("/turtles/new")}>
                    + Yeni Kaplumbağa Kaydı
                  </button>
                </>
              )}

              <button className="btn-ghost" style={{ width: "100%", borderRadius: 11 }} onClick={handleReset}>
                Yeni Sorgulama
              </button>
            </div>
          </div>
        )}

        {/* ── CANDIDATES ── */}
        {state === "candidates" && result && (
          <div className="fade-up" style={{ marginTop: "1.5rem", borderRadius: 24, background: "#fff", boxShadow: "0 20px 60px rgba(12,74,110,.15)", overflow: "hidden", border: "1px solid rgba(255,255,255,.9)" }}>
            <div style={{ background: "linear-gradient(135deg,#d97706,#b45309)", padding: "1.2rem 1.75rem", display: "flex", alignItems: "center", gap: ".85rem" }}>
              <div style={{ width: 42, height: 42, borderRadius: "50%", background: "rgba(255,255,255,.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.3rem" }}>🔎</div>
              <div>
                <div style={{ fontWeight: 800, color: "#fff", fontSize: "1rem" }}>Kesin eşleşme bulunamadı</div>
                <div style={{ fontSize: ".8rem", color: "rgba(255,255,255,.75)" }}>Olası benzer kaplumbağalar listelendi</div>
              </div>
            </div>
            <div style={{ padding: "1.75rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: ".5rem", marginBottom: ".85rem" }}>
                <span style={{ fontWeight: 700, fontSize: ".88rem", color: "#0f172a" }}>Olası Benzerlikler</span>
                <span style={{ fontSize: ".68rem", color: "#d97706", background: "#fef3c7", padding: ".13rem .55rem", borderRadius: 99, fontWeight: 700, border: "1px solid #fde68a" }}>onaysız</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: ".45rem", marginBottom: "1.5rem" }}>
                {result.candidates.map(m => (
                  <MatchRow key={m.turtle_id.toString()} m={m} onClick={() => navigate(`/turtles/${m.turtle_id.toString()}`)} />
                ))}
              </div>
              <hr className="divider" />
              <div style={{ background: "#f0fdf4", border: "1.5px solid #6ee7b7", borderRadius: 13, padding: "1rem 1.1rem", marginBottom: ".85rem" }}>
                <div style={{ fontWeight: 800, fontSize: ".85rem", color: "#065f46", marginBottom: ".2rem" }}>Kayıtlı değil mi?</div>
                <div style={{ fontSize: ".8rem", color: "#047857" }}>Yeni profil oluşturarak veritabanına ekleyebilirsiniz.</div>
              </div>
              <button className="btn-primary" style={{ width: "100%", padding: ".85rem", borderRadius: 13, marginBottom: ".6rem" }}
                onClick={() => navigate("/turtles/new")}>
                + Yeni Kaplumbağa Kaydı
              </button>
              <button className="btn-ghost" style={{ width: "100%", borderRadius: 11 }} onClick={handleReset}>Yeni Sorgulama</button>
            </div>
          </div>
        )}

        {/* ── NOT FOUND ── */}
        {state === "notfound" && (
          <div className="fade-up" style={{ marginTop: "1.5rem", borderRadius: 24, background: "#fff", boxShadow: "0 20px 60px rgba(12,74,110,.15)", overflow: "hidden" }}>
            <div style={{ background: "linear-gradient(135deg,#dc2626,#b91c1c)", padding: "1.2rem 1.75rem", display: "flex", alignItems: "center", gap: ".85rem" }}>
              <div style={{ width: 42, height: 42, borderRadius: "50%", background: "rgba(255,255,255,.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.3rem" }}>🔍</div>
              <div>
                <div style={{ fontWeight: 800, color: "#fff" }}>Kayıtlı kaplumbağa bulunamadı</div>
                <div style={{ fontSize: ".8rem", color: "rgba(255,255,255,.72)" }}>Bu birey sistemde kayıtlı değil</div>
              </div>
            </div>
            <div style={{ padding: "1.75rem" }}>
              <p style={{ color: "#64748b", fontSize: ".9rem", marginBottom: "1.5rem", lineHeight: 1.7 }}>
                Fotoğraf ile kayıtlı hiçbir kaplumbağa arasında yeterli benzerlik tespit edilemedi. Yeni bir profil oluşturabilirsiniz.
              </p>
              <button className="btn-primary" style={{ width: "100%", padding: ".85rem", borderRadius: 13, marginBottom: ".65rem" }}
                onClick={() => navigate("/turtles/new")}>
                + Yeni Kaplumbağa Kaydı
              </button>
              <button className="btn-ghost" style={{ width: "100%", borderRadius: 11 }} onClick={handleReset}>Tekrar Dene</button>
            </div>
          </div>
        )}

        {/* ── NO TURTLE ── */}
        {state === "noturtle" && (
          <div className="fade-up" style={{ marginTop: "1.5rem", borderRadius: 24, background: "#fff", boxShadow: "0 20px 60px rgba(12,74,110,.15)", overflow: "hidden" }}>
            <div style={{ background: "linear-gradient(135deg,#64748b,#475569)", padding: "1.2rem 1.75rem", display: "flex", alignItems: "center", gap: ".85rem" }}>
              <div style={{ width: 42, height: 42, borderRadius: "50%", background: "rgba(255,255,255,.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.3rem" }}>🚫</div>
              <div>
                <div style={{ fontWeight: 800, color: "#fff" }}>Fotoğrafta kaplumbağa bulunamadı</div>
                <div style={{ fontSize: ".8rem", color: "rgba(255,255,255,.72)" }}>Yapay zeka bu görselde kaplumbağa tespit edemedi</div>
              </div>
            </div>
            <div style={{ padding: "2rem", textAlign: "center" }}>
              <div style={{ fontSize: "3.5rem", marginBottom: "1rem", opacity: .18 }}>🐢</div>
              <p style={{ fontWeight: 800, color: "#0f172a", marginBottom: ".4rem", fontSize: ".95rem" }}>Lütfen kaplumbağa içeren bir fotoğraf yükleyin</p>
              <p style={{ color: "#64748b", fontSize: ".85rem", marginBottom: "1.75rem", lineHeight: 1.7, maxWidth: 340, margin: "0 auto 1.75rem" }}>
                Sistem önce fotoğrafta kaplumbağa olup olmadığını doğrular. Stadyum, araba veya kişi görselleri kabul edilmez.
              </p>
              <button className="btn-primary" style={{ borderRadius: 11 }} onClick={handleReset}>Farklı Fotoğraf Dene</button>
            </div>
          </div>
        )}

        {/* ── ERROR ── */}
        {state === "error" && (
          <div className="fade-up" style={{ marginTop: "1.5rem", borderRadius: 24, background: "#fff", boxShadow: "0 20px 60px rgba(12,74,110,.12)", overflow: "hidden" }}>
            <div style={{ background: "linear-gradient(135deg,#dc2626,#b91c1c)", padding: "1.1rem 1.75rem" }}>
              <span style={{ fontWeight: 800, color: "#fff" }}>Hata oluştu</span>
            </div>
            <div style={{ padding: "1.5rem" }}>
              <p style={{ color: "#64748b", fontSize: ".88rem", marginBottom: "1rem" }}>{errorMsg}</p>
              <button className="btn-ghost" onClick={handleReset}>Tekrar Dene</button>
            </div>
          </div>
        )}

        {/* ── Feature strip (idle) ── */}
        {state === "idle" && (
          <div className="fade-up" style={{ marginTop: "2.5rem", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: ".75rem" }}>
            {[
              { icon: "🎯", title: "Hassas Tespit", desc: "4 aşamalı ML boru hattı" },
              { icon: "🗂️", title: "Bireysel Tanıma", desc: "3-bölge karapaks analizi" },
              { icon: "📍", title: "Konum Takibi", desc: "GPS gözlem haritası" },
            ].map(f => (
              <div key={f.title} style={{ background: "rgba(255,255,255,.7)", backdropFilter: "blur(8px)", borderRadius: 16, padding: "1.1rem", textAlign: "center", border: "1px solid rgba(255,255,255,.8)", boxShadow: "0 4px 16px rgba(12,74,110,.06)" }}>
                <div style={{ fontSize: "1.6rem", marginBottom: ".5rem" }}>{f.icon}</div>
                <div style={{ fontWeight: 800, fontSize: ".82rem", color: "#0f172a", marginBottom: ".2rem" }}>{f.title}</div>
                <div style={{ fontSize: ".72rem", color: "#64748b" }}>{f.desc}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
