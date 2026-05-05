import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { turtleApi, type Turtle } from "../services/api";

const PALETTE = ["#0d9488","#0891b2","#7c3aed","#db2777","#ea580c","#16a34a","#ca8a04","#0369a1"];
const color = (name: string) => PALETTE[name.charCodeAt(0) % PALETTE.length];

export default function TurtleListPage() {
  const navigate = useNavigate();
  const [turtles, setTurtles] = useState<Turtle[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");
  const [error, setError]     = useState("");

  useEffect(() => {
    turtleApi.list()
      .then(setTurtles)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = turtles.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page">

      {/* ── Header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "2rem" }}>
        <div>
          <p style={{ fontSize: ".78rem", fontWeight: 700, color: "var(--teal)", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: ".3rem" }}>
            Veritabanı
          </p>
          <h1 style={{ fontSize: "2rem", fontWeight: 900, color: "var(--ink)", letterSpacing: "-.03em", lineHeight: 1.1 }}>
            Kaplumbağalar
          </h1>
          {!loading && (
            <p style={{ color: "var(--muted)", fontSize: ".875rem", marginTop: ".3rem" }}>
              {turtles.length} kayıtlı birey
            </p>
          )}
        </div>
        <Link to="/turtles/new" className="btn-primary" style={{ borderRadius: 10, padding: ".6rem 1.2rem" }}>
          + Yeni Kayıt
        </Link>
      </div>

      {/* ── Search ── */}
      <div style={{ position: "relative", maxWidth: 360, marginBottom: "2rem" }}>
        <svg style={{ position: "absolute", left: "1rem", top: "50%", transform: "translateY(-50%)", width: 16, height: 16, color: "var(--muted)", pointerEvents: "none" }}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input
          type="search"
          placeholder="İsme göre ara…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ paddingLeft: "2.6rem", borderRadius: 10 }}
        />
      </div>

      {/* ── States ── */}
      {loading && (
        <div style={{ display: "flex", justifyContent: "center", padding: "5rem 0" }}>
          <div className="spinner" />
        </div>
      )}

      {error && (
        <div className="card" style={{ color: "var(--danger)", borderColor: "#fecaca" }}>
          Hata: {error}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div style={{
          textAlign: "center", padding: "5rem 2rem",
          background: "var(--white)", borderRadius: 24,
          border: "1px dashed var(--border)",
          boxShadow: "var(--shadow)",
        }}>
          <div style={{ fontSize: "4rem", marginBottom: "1rem", opacity: .2, filter: "grayscale(1)" }}>🐢</div>
          {search ? (
            <>
              <p style={{ fontWeight: 700, marginBottom: ".4rem" }}>"{search}" için sonuç bulunamadı</p>
              <p style={{ color: "var(--muted)", fontSize: ".875rem" }}>Farklı bir isim deneyin.</p>
            </>
          ) : (
            <>
              <p style={{ fontWeight: 800, fontSize: "1.1rem", marginBottom: ".5rem" }}>Henüz kayıt yok</p>
              <p style={{ color: "var(--muted)", fontSize: ".9rem", marginBottom: "1.5rem" }}>İlk kaplumbağayı kaydederek başlayın.</p>
              <Link to="/turtles/new" className="btn-primary" style={{ display: "inline-flex", borderRadius: 10 }}>
                İlk kaydı oluştur
              </Link>
            </>
          )}
        </div>
      )}

      {/* ── Grid ── */}
      <div className="grid-3">
        {filtered.map((t) => {
          const c = color(t.name);
          const initials = t.name.charAt(0).toUpperCase();
          const regDate = new Date(t.registered_at).toLocaleDateString("tr-TR", { day: "numeric", month: "short", year: "numeric" });

          return (
            <div
              key={t.id}
              onClick={() => navigate(`/turtles/${t.id}`)}
              className="card card-hover"
              style={{
                cursor: "pointer", padding: 0, overflow: "hidden",
                borderRadius: 20,
              }}
            >
              {/* Card top stripe */}
              <div style={{
                height: 6,
                background: `linear-gradient(90deg, ${c}, ${c}99)`,
              }} />

              <div style={{ padding: "1.25rem" }}>
                {/* Avatar + name */}
                <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
                  <div style={{
                    width: 50, height: 50, borderRadius: "50%",
                    background: `linear-gradient(135deg, ${c}, ${c}bb)`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "1.25rem", fontWeight: 900, color: "#fff",
                    boxShadow: `0 4px 14px ${c}44`, flexShrink: 0,
                    letterSpacing: "-.01em",
                  }}>
                    {initials}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 800, fontSize: "1.05rem", color: "var(--ink)", letterSpacing: "-.01em" }}>
                      {t.name}
                    </div>
                    <div style={{ fontSize: ".75rem", color: "var(--subtle)", marginTop: ".1rem" }}>
                      {regDate}
                    </div>
                  </div>
                </div>

                {/* Notes */}
                {t.notes && (
                  <p style={{
                    fontSize: ".8rem", color: "var(--muted)",
                    overflow: "hidden", display: "-webkit-box",
                    WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
                    lineHeight: 1.5, marginBottom: ".85rem",
                  }}>
                    {t.notes}
                  </p>
                )}

                {/* Footer chip */}
                <div style={{ display: "flex", alignItems: "center", gap: ".4rem" }}>
                  <div style={{
                    display: "inline-flex", alignItems: "center", gap: ".3rem",
                    background: `${c}12`, color: c,
                    padding: ".22rem .7rem", borderRadius: 99,
                    fontSize: ".72rem", fontWeight: 700,
                  }}>
                    <span>🐢</span> Profili görüntüle
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
