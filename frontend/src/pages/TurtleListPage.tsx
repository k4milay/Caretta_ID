import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { turtleApi, type Turtle } from "../services/api";

const PALETTE = ["#0d9488","#0891b2","#7c3aed","#db2777","#ea580c","#16a34a","#ca8a04","#0369a1"];
const avatarColor = (name: string) => PALETTE[name.charCodeAt(0) % PALETTE.length];

export default function TurtleListPage() {
  const navigate = useNavigate();
  const [turtles, setTurtles] = useState<Turtle[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");
  const [error, setError]     = useState("");

  useEffect(() => {
    turtleApi.list()
      .then(setTurtles)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = turtles.filter(t => t.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      {/* ── Page header banner ── */}
      <div style={{
        background: "linear-gradient(135deg, #0a2540 0%, #0c4a6e 60%, #0d9488 100%)",
        padding: "3.5rem 2rem 5rem",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{ position: "absolute", width: 400, height: 400, borderRadius: "50%", background: "rgba(255,255,255,.03)", top: -100, right: -80, pointerEvents: "none" }} />
        <div style={{ maxWidth: 1080, margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: "1.5rem", flexWrap: "wrap" }}>
          <div>
            <p style={{ fontSize: ".72rem", fontWeight: 800, color: "rgba(153,246,228,.85)", textTransform: "uppercase", letterSpacing: ".12em", marginBottom: ".5rem" }}>
              Veritabanı
            </p>
            <h1 style={{ fontSize: "clamp(1.8rem,4vw,2.6rem)", fontWeight: 900, color: "#fff", letterSpacing: "-.04em", lineHeight: 1.1, marginBottom: ".5rem" }}>
              Kayıtlı Kaplumbağalar
            </h1>
            {!loading && (
              <p style={{ color: "rgba(255,255,255,.6)", fontSize: ".9rem" }}>
                {turtles.length} bireysel profil
              </p>
            )}
          </div>
          <Link to="/turtles/new" className="btn-primary" style={{ borderRadius: 12, padding: ".7rem 1.4rem", fontSize: ".9rem", textDecoration: "none" }}>
            + Yeni Kayıt
          </Link>
        </div>
      </div>

      <div className="page" style={{ marginTop: "-3rem", paddingTop: 0 }}>

        {/* ── Search ── */}
        <div style={{ maxWidth: 400, marginBottom: "2rem" }}>
          <div style={{ position: "relative" }}>
            <svg style={{ position: "absolute", left: "1rem", top: "50%", transform: "translateY(-50%)", width: 17, height: 17, color: "#94a3b8", pointerEvents: "none" }}
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            <input
              type="search"
              placeholder="İsme göre ara…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: "2.75rem", borderRadius: 12, fontSize: ".9rem" }}
            />
          </div>
        </div>

        {/* ── States ── */}
        {loading && (
          <div style={{ display: "flex", justifyContent: "center", padding: "6rem 0" }}>
            <div className="spinner" />
          </div>
        )}

        {error && (
          <div className="card" style={{ color: "var(--danger)", borderColor: "#fecaca" }}>Hata: {error}</div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div style={{ textAlign: "center", padding: "6rem 2rem", background: "#fff", borderRadius: 24, border: "2px dashed #e2e8f0", boxShadow: "var(--shadow)" }}>
            <div style={{ fontSize: "4.5rem", marginBottom: "1.25rem", opacity: .15, filter: "grayscale(1)" }}>🐢</div>
            {search ? (
              <>
                <p style={{ fontWeight: 800, fontSize: "1rem", marginBottom: ".4rem" }}>"{search}" için sonuç yok</p>
                <p style={{ color: "#64748b", fontSize: ".88rem" }}>Farklı bir isim deneyin.</p>
              </>
            ) : (
              <>
                <p style={{ fontWeight: 900, fontSize: "1.15rem", marginBottom: ".5rem" }}>Henüz kayıt yok</p>
                <p style={{ color: "#64748b", fontSize: ".9rem", marginBottom: "1.75rem" }}>İlk kaplumbağayı kaydederek başlayın.</p>
                <Link to="/turtles/new" className="btn-primary" style={{ display: "inline-flex", borderRadius: 11, textDecoration: "none" }}>
                  İlk Kaydı Oluştur
                </Link>
              </>
            )}
          </div>
        )}

        {/* ── Grid ── */}
        <div className="grid-3">
          {filtered.map(t => {
            const c = avatarColor(t.name);
            const regDate = new Date(t.registered_at).toLocaleDateString("tr-TR", { day: "numeric", month: "short", year: "numeric" });

            return (
              <div
                key={t.id}
                onClick={() => navigate(`/turtles/${t.id}`)}
                style={{
                  cursor: "pointer",
                  background: "#fff",
                  borderRadius: 20,
                  overflow: "hidden",
                  border: "1.5px solid rgba(226,232,240,.6)",
                  boxShadow: "0 4px 16px rgba(15,23,42,.07)",
                  transition: "all .22s cubic-bezier(.4,0,.2,1)",
                }}
                onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-5px)"; e.currentTarget.style.boxShadow = `0 16px 40px ${c}28, 0 4px 12px rgba(15,23,42,.08)`; e.currentTarget.style.borderColor = `${c}40`; }}
                onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = "0 4px 16px rgba(15,23,42,.07)"; e.currentTarget.style.borderColor = "rgba(226,232,240,.6)"; }}
              >
                {/* Top stripe */}
                <div style={{ height: 5, background: `linear-gradient(90deg, ${c}, ${c}99)` }} />

                <div style={{ padding: "1.35rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: ".9rem" }}>
                    <div style={{
                      width: 52, height: 52, borderRadius: "50%",
                      background: `linear-gradient(135deg, ${c}, ${c}bb)`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: "1.3rem", fontWeight: 900, color: "#fff",
                      boxShadow: `0 4px 14px ${c}44`, flexShrink: 0,
                    }}>
                      {t.name.charAt(0).toUpperCase()}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 800, fontSize: "1.05rem", color: "#0f172a", letterSpacing: "-.01em", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.name}</div>
                      <div style={{ fontSize: ".73rem", color: "#94a3b8", marginTop: ".12rem" }}>{regDate}</div>
                    </div>
                  </div>

                  {t.notes && (
                    <p style={{ fontSize: ".8rem", color: "#64748b", overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", lineHeight: 1.55, marginBottom: ".9rem" }}>
                      {t.notes}
                    </p>
                  )}

                  <div style={{ display: "inline-flex", alignItems: "center", gap: ".3rem", background: `${c}12`, color: c, padding: ".25rem .75rem", borderRadius: 99, fontSize: ".72rem", fontWeight: 700 }}>
                    🐢 Profili görüntüle
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
