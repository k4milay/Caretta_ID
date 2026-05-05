import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DropZone from "../components/DropZone";
import { identifyApi, type IdentificationResponse, type MatchResult } from "../services/api";

type State = "idle" | "loading" | "found" | "candidates" | "notfound" | "noturtle" | "error";

const CONF_COLORS: Record<string, string> = {
  high:   "#10b981",
  medium: "#f59e0b",
  low:    "#f97316",
};

const CONF_LABELS: Record<string, string> = {
  high:   "Yüksek güven",
  medium: "Orta güven",
  low:    "Düşük güven",
};

function ScoreBar({ score, color }: { score: number; color: string }) {
  const pct = Math.round(score * 100);
  return (
    <div style={{ height: 8, background: "#f1f5f9", borderRadius: 99, overflow: "hidden" }}>
      <div style={{
        height: "100%", borderRadius: 99,
        width: `${pct}%`,
        background: `linear-gradient(90deg, ${color}99, ${color})`,
        transition: "width .7s cubic-bezier(.4,0,.2,1)",
        boxShadow: `0 0 6px ${color}55`,
      }} />
    </div>
  );
}

function MatchRow({ m, onClick }: { m: MatchResult; onClick: () => void }) {
  const pct = Math.round(m.similarity_score * 100);
  // Renk ve etiket direkt confidence bantlarından türetilir
  const color = pct >= 76 ? "#10b981" : pct >= 73 ? "#f59e0b" : "#f97316";
  return (
    <div
      onClick={onClick}
      style={{
        display: "flex", alignItems: "center", gap: ".85rem",
        padding: ".7rem .9rem", borderRadius: 12, cursor: "pointer",
        border: "1px solid var(--border)", background: "var(--bg)",
        transition: "all .15s",
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = "#fff"; e.currentTarget.style.boxShadow = "var(--shadow)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = "var(--bg)"; e.currentTarget.style.boxShadow = "none"; }}>
      <div style={{
        width: 38, height: 38, borderRadius: "50%", flexShrink: 0,
        background: `linear-gradient(135deg, ${color}, ${color}bb)`,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "1rem", fontWeight: 900, color: "#fff",
        boxShadow: `0 3px 10px ${color}44`,
      }}>
        {m.name.charAt(0).toUpperCase()}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: ".9rem", color: "var(--ink)" }}>{m.name}</div>
        <ScoreBar score={m.similarity_score} color={color} />
      </div>
      <div style={{ textAlign: "right", flexShrink: 0 }}>
        <div style={{ fontSize: "1.15rem", fontWeight: 900, color, letterSpacing: "-.01em" }}>{pct}%</div>
        <div style={{
          fontSize: ".62rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".05em",
          color, background: `${color}18`, padding: ".12rem .45rem", borderRadius: 99,
        }}>
          {CONF_LABELS[m.confidence] ?? m.confidence}
        </div>
      </div>
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
      if (!res.turtle_detected) {
        setState("noturtle");
      } else if (res.accepted) {
        setState("found");
      } else if (res.candidates && res.candidates.length > 0) {
        setState("candidates");
      } else {
        setState("notfound");
      }
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Bir hata oluştu.");
      setState("error");
    }
  }

  function handleReset() { setFile(null); setState("idle"); setResult(null); }

  const top = result?.matches?.[0];
  const topPct = top ? Math.round(top.similarity_score * 100) : 0;
  // Eşleşme confidence bantlarıyla tutarlı: ≥76% yeşil, ≥73% amber, altı turuncu
  const barColor = topPct >= 76 ? "#10b981" : topPct >= 73 ? "#f59e0b" : "#f97316";
  const showNewRegister = !result?.accepted || topPct < 76;

  return (
    <div style={{ minHeight: "calc(100vh - 66px)", background: "linear-gradient(170deg, #0c4a6e 0%, #0d9488 45%, #f0f6f5 100%)" }}>

      {/* ── Hero ── */}
      <div style={{ textAlign: "center", padding: "4rem 1.25rem 2.5rem", color: "#fff" }}>
        <div style={{
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          width: 80, height: 80, borderRadius: "50%",
          background: "rgba(255,255,255,.15)",
          backdropFilter: "blur(12px)",
          border: "1.5px solid rgba(255,255,255,.25)",
          boxShadow: "0 8px 32px rgba(0,0,0,.2)",
          marginBottom: "1.25rem", fontSize: "2.2rem",
        }}>🐢</div>
        <h1 style={{ fontSize: "2.4rem", fontWeight: 900, letterSpacing: "-.03em", marginBottom: ".5rem", textShadow: "0 2px 20px rgba(0,0,0,.2)" }}>
          Kaplumbağa Tanımlama
        </h1>
        <p style={{ color: "rgba(255,255,255,.75)", fontSize: "1rem", maxWidth: 380, margin: "0 auto" }}>
          Fotoğraf yükleyin — sistem saniyeler içinde benzerlik analizi yapsın
        </p>
      </div>

      {/* ── Card ── */}
      <div style={{ maxWidth: 580, margin: "0 auto", padding: "0 1.25rem 4rem" }}>

        {/* Upload */}
        <div style={{
          background: "var(--white)", borderRadius: 24, padding: "1.75rem",
          boxShadow: "0 24px 64px rgba(12,74,110,.25), 0 4px 16px rgba(0,0,0,.08)",
          border: "1px solid rgba(255,255,255,.8)",
        }}>
          <DropZone onFile={(f) => { setFile(f); setState("idle"); setResult(null); }} />

          {file && state === "idle" && (
            <button className="btn-primary fade-up"
              style={{ width: "100%", marginTop: "1.1rem", padding: ".85rem", fontSize: "1rem", borderRadius: 12 }}
              onClick={handleQuery}>
              Analiz Et
            </button>
          )}

          {state === "loading" && (
            <div style={{ textAlign: "center", padding: "1.5rem 0 .5rem" }}>
              <div className="spinner" style={{ margin: "0 auto .85rem" }} />
              <p style={{ color: "var(--muted)", fontWeight: 500, fontSize: ".9rem" }}>Görüntü analiz ediliyor…</p>
            </div>
          )}
        </div>

        {/* ── FOUND ── */}
        {state === "found" && top && (
          <div className="fade-up" style={{
            marginTop: "1.25rem", borderRadius: 24,
            background: "var(--white)",
            boxShadow: "0 16px 48px rgba(12,74,110,.18), 0 4px 12px rgba(0,0,0,.06)",
            overflow: "hidden",
            border: "1px solid rgba(255,255,255,.8)",
          }}>
            {/* Status bar */}
            <div style={{ background: "linear-gradient(135deg,#0d9488,#0891b2)", padding: "1rem 1.5rem", display: "flex", alignItems: "center", gap: ".75rem" }}>
              <span style={{ fontSize: "1.3rem" }}>✅</span>
              <div>
                <div style={{ fontWeight: 700, color: "#fff", fontSize: ".95rem" }}>Kayıtlı kaplumbağa bulundu</div>
                <div style={{ fontSize: ".78rem", color: "rgba(255,255,255,.7)" }}>Sistemde eşleşen kayıt var</div>
              </div>
            </div>

            <div style={{ padding: "1.5rem" }}>
              {/* Main match */}
              <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.1rem" }}>
                <div style={{
                  width: 56, height: 56, borderRadius: "50%", flexShrink: 0,
                  background: `linear-gradient(135deg, ${barColor}, ${barColor}bb)`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "1.5rem", fontWeight: 900, color: "#fff",
                  boxShadow: `0 4px 14px ${barColor}44`,
                }}>
                  {top.name.charAt(0).toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: ".72rem", fontWeight: 700, color: "var(--teal)", textTransform: "uppercase", letterSpacing: ".07em" }}>En yakın eşleşme</div>
                  <div style={{ fontSize: "1.45rem", fontWeight: 900, color: "var(--ink)", letterSpacing: "-.01em", lineHeight: 1.2 }}>{top.name}</div>
                </div>
                <div style={{ textAlign: "right", flexShrink: 0 }}>
                  <div style={{ fontSize: "2.4rem", fontWeight: 900, color: barColor, lineHeight: 1, letterSpacing: "-.02em" }}>{topPct}%</div>
                  <div style={{
                    fontSize: ".68rem", fontWeight: 700, letterSpacing: ".05em", textTransform: "uppercase",
                    color: CONF_COLORS[top.confidence] ?? "var(--muted)",
                    background: `${CONF_COLORS[top.confidence] ?? "#94a3b8"}18`,
                    padding: ".18rem .55rem", borderRadius: 99, marginTop: ".2rem", display: "inline-block",
                  }}>
                    {CONF_LABELS[top.confidence] ?? top.confidence}
                  </div>
                </div>
              </div>

              {/* Bar */}
              <div style={{ marginBottom: "1.1rem" }}>
                <ScoreBar score={top.similarity_score} color={barColor} />
              </div>

              <button className="btn-primary"
                style={{ width: "100%", padding: ".8rem", borderRadius: 12, fontSize: ".95rem", marginBottom: ".75rem" }}
                onClick={() => navigate(`/turtles/${top.turtle_id.toString()}`)}>
                Profilini Görüntüle →
              </button>

              {/* Other accepted matches */}
              {result!.matches.length > 1 && (
                <>
                  <hr className="divider" />
                  <div className="section-title" style={{ marginBottom: ".6rem" }}>Diğer eşleşmeler</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: ".4rem" }}>
                    {result!.matches.slice(1).map((m) => (
                      <MatchRow key={m.turtle_id.toString()} m={m} onClick={() => navigate(`/turtles/${m.turtle_id.toString()}`)} />
                    ))}
                  </div>
                </>
              )}

              {/* Candidate matches below threshold */}
              {result!.candidates && result!.candidates.length > 0 && (
                <>
                  <hr className="divider" />
                  <div style={{ display: "flex", alignItems: "center", gap: ".5rem", marginBottom: ".6rem" }}>
                    <div className="section-title" style={{ margin: 0 }}>Düşük benzerlikli adaylar</div>
                    <span style={{ fontSize: ".7rem", color: "var(--muted)", background: "var(--bg)", padding: ".15rem .5rem", borderRadius: 99, border: "1px solid var(--border)" }}>
                      eşik altı
                    </span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: ".4rem" }}>
                    {result!.candidates.map((m) => (
                      <MatchRow key={m.turtle_id.toString()} m={m} onClick={() => navigate(`/turtles/${m.turtle_id.toString()}`)} />
                    ))}
                  </div>
                </>
              )}

              {/* New register prompt if confidence is low */}
              {showNewRegister && (
                <>
                  <hr className="divider" />
                  <div style={{
                    background: "linear-gradient(135deg, #fef3c7, #fde68a)",
                    border: "1px solid #fcd34d",
                    borderRadius: 12, padding: "1rem",
                    marginBottom: ".75rem",
                  }}>
                    <div style={{ fontWeight: 700, fontSize: ".85rem", color: "#92400e", marginBottom: ".25rem" }}>
                      Bu kaplumbağa mı?
                    </div>
                    <div style={{ fontSize: ".8rem", color: "#78350f" }}>
                      Eşleşme %80 altında. Yeni bir profil oluşturmak ister misiniz?
                    </div>
                  </div>
                  <button className="btn-primary" style={{ width: "100%", borderRadius: 10, background: "linear-gradient(135deg,#d97706,#b45309)" }}
                    onClick={() => navigate("/turtles/new")}>
                    + Yeni Kaplumbağa Kaydı Oluştur
                  </button>
                </>
              )}

              <button className="btn-ghost" style={{ width: "100%", marginTop: ".75rem", borderRadius: 10 }} onClick={handleReset}>
                Yeni Sorgulama
              </button>
            </div>
          </div>
        )}

        {/* ── CANDIDATES (below threshold but above floor) ── */}
        {state === "candidates" && result && (
          <div className="fade-up" style={{
            marginTop: "1.25rem", borderRadius: 24, overflow: "hidden",
            background: "var(--white)",
            boxShadow: "0 16px 48px rgba(12,74,110,.18), 0 4px 12px rgba(0,0,0,.06)",
            border: "1px solid rgba(255,255,255,.8)",
          }}>
            {/* Status bar — amber */}
            <div style={{ background: "linear-gradient(135deg,#d97706,#b45309)", padding: "1rem 1.5rem", display: "flex", alignItems: "center", gap: ".75rem" }}>
              <span style={{ fontSize: "1.3rem" }}>🔎</span>
              <div>
                <div style={{ fontWeight: 700, color: "#fff", fontSize: ".95rem" }}>Kesin eşleşme bulunamadı</div>
                <div style={{ fontSize: ".78rem", color: "rgba(255,255,255,.75)" }}>
                  Olası benzer kaplumbağalar aşağıda listelendi
                </div>
              </div>
            </div>

            <div style={{ padding: "1.5rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: ".5rem", marginBottom: ".8rem" }}>
                <div style={{ fontWeight: 700, fontSize: ".85rem", color: "var(--ink)" }}>Olası Benzerlikler</div>
                <span style={{
                  fontSize: ".7rem", color: "#d97706", background: "#fef3c7",
                  padding: ".15rem .55rem", borderRadius: 99, fontWeight: 700,
                  border: "1px solid #fcd34d",
                }}>
                  eşik altı — onaysız
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: ".4rem", marginBottom: "1.25rem" }}>
                {result.candidates.map((m) => (
                  <MatchRow key={m.turtle_id.toString()} m={m} onClick={() => navigate(`/turtles/${m.turtle_id.toString()}`)} />
                ))}
              </div>

              <hr className="divider" />

              {/* New register call-to-action */}
              <div style={{
                background: "linear-gradient(135deg,#ecfdf5,#d1fae5)",
                border: "1px solid #6ee7b7",
                borderRadius: 12, padding: "1rem 1.1rem",
                marginBottom: ".85rem",
              }}>
                <div style={{ fontWeight: 700, fontSize: ".88rem", color: "#065f46", marginBottom: ".2rem" }}>
                  Bu kaplumbağa kayıtlı değil mi?
                </div>
                <div style={{ fontSize: ".8rem", color: "#047857" }}>
                  Yukarıdaki sonuçlar emin olunacak benzerliğe ulaşamadı. Yeni bir profil oluşturabilirsiniz.
                </div>
              </div>

              <button className="btn-primary"
                style={{ width: "100%", padding: ".85rem", borderRadius: 12, fontSize: ".95rem", marginBottom: ".6rem" }}
                onClick={() => navigate("/turtles/new")}>
                + Yeni Kaplumbağa Kaydı Oluştur
              </button>

              <button className="btn-ghost" style={{ width: "100%", borderRadius: 10 }} onClick={handleReset}>
                Yeni Sorgulama
              </button>
            </div>
          </div>
        )}

        {/* ── NOT FOUND ── */}
        {state === "notfound" && (
          <div className="fade-up" style={{
            marginTop: "1.25rem", borderRadius: 24, overflow: "hidden",
            background: "var(--white)",
            boxShadow: "0 16px 48px rgba(12,74,110,.18)",
          }}>
            <div style={{ background: "linear-gradient(135deg,#dc2626,#b91c1c)", padding: "1rem 1.5rem", display: "flex", alignItems: "center", gap: ".75rem" }}>
              <span style={{ fontSize: "1.3rem" }}>🔍</span>
              <div>
                <div style={{ fontWeight: 700, color: "#fff" }}>Hiç benzerlik bulunamadı</div>
                <div style={{ fontSize: ".78rem", color: "rgba(255,255,255,.7)" }}>Bu kaplumbağa sistemde kayıtlı değil</div>
              </div>
            </div>
            <div style={{ padding: "1.75rem" }}>
              <p style={{ color: "var(--muted)", fontSize: ".9rem", marginBottom: "1.5rem" }}>
                Sistem bu fotoğraf ile herhangi bir kayıtlı kaplumbağa arasında benzerlik tespit edemedi.
                Yeni bir profil oluşturarak veritabanına ekleyebilirsiniz.
              </p>
              <button className="btn-primary"
                style={{ width: "100%", padding: ".85rem", borderRadius: 12, marginBottom: ".65rem" }}
                onClick={() => navigate("/turtles/new")}>
                + Yeni Kaplumbağa Kaydı Oluştur
              </button>
              <button className="btn-ghost" style={{ width: "100%", borderRadius: 10 }} onClick={handleReset}>
                Tekrar Dene
              </button>
            </div>
          </div>
        )}

        {/* ── NO TURTLE DETECTED ── */}
        {state === "noturtle" && (
          <div className="fade-up" style={{
            marginTop: "1.25rem", borderRadius: 24, overflow: "hidden",
            background: "var(--white)",
            boxShadow: "0 16px 48px rgba(12,74,110,.18)",
          }}>
            <div style={{ background: "linear-gradient(135deg,#64748b,#475569)", padding: "1rem 1.5rem", display: "flex", alignItems: "center", gap: ".75rem" }}>
              <span style={{ fontSize: "1.3rem" }}>🚫</span>
              <div>
                <div style={{ fontWeight: 700, color: "#fff" }}>Fotoğrafta kaplumbağa bulunamadı</div>
                <div style={{ fontSize: ".78rem", color: "rgba(255,255,255,.7)" }}>Yapay zeka bu görselde kaplumbağa tespit edemedi</div>
              </div>
            </div>
            <div style={{ padding: "1.75rem", textAlign: "center" }}>
              <div style={{ fontSize: "3rem", marginBottom: ".75rem", opacity: .25 }}>🐢</div>
              <p style={{ color: "var(--ink)", fontWeight: 700, marginBottom: ".4rem" }}>
                Lütfen kaplumbağa içeren bir fotoğraf yükleyin
              </p>
              <p style={{ color: "var(--muted)", fontSize: ".88rem", marginBottom: "1.5rem" }}>
                Sistem önce fotoğrafta kaplumbağa olup olmadığını doğrular, ardından kimlik karşılaştırması yapar. Stadyum, araba, kişi gibi görseller kabul edilmez.
              </p>
              <button className="btn-primary" style={{ borderRadius: 10 }} onClick={handleReset}>
                Farklı Fotoğraf Dene
              </button>
            </div>
          </div>
        )}

        {/* ── ERROR ── */}
        {state === "error" && (
          <div className="fade-up" style={{
            marginTop: "1.25rem", borderRadius: 24, overflow: "hidden",
            background: "var(--white)", boxShadow: "var(--shadow-md)",
          }}>
            <div style={{ background: "linear-gradient(135deg,#dc2626,#b91c1c)", padding: "1rem 1.5rem" }}>
              <span style={{ fontWeight: 700, color: "#fff" }}>Hata oluştu</span>
            </div>
            <div style={{ padding: "1.5rem" }}>
              <p style={{ color: "var(--muted)", fontSize: ".88rem", marginBottom: "1rem" }}>{errorMsg}</p>
              <button className="btn-ghost" onClick={handleReset}>Tekrar Dene</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
