import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { turtleApi, type Turtle } from "../services/api";

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

  const COLORS = ["#0d9488","#0891b2","#7c3aed","#db2777","#ea580c","#16a34a"];
  const color = (name: string) => COLORS[name.charCodeAt(0) % COLORS.length];

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ fontSize: "1.7rem", fontWeight: 900, color: "var(--ink)", letterSpacing: "-.02em" }}>Kaplumbağalar</h1>
          <p style={{ color: "var(--muted)", fontSize: ".88rem", marginTop: ".2rem" }}>{turtles.length} kayıtlı birey</p>
        </div>
        <Link to="/turtles/new" className="btn-primary" style={{ borderRadius: 9 }}>+ Yeni Kayıt</Link>
      </div>

      <div style={{ position: "relative", maxWidth: 340, marginBottom: "1.75rem" }}>
        <span style={{ position: "absolute", left: ".9rem", top: "50%", transform: "translateY(-50%)", color: "var(--muted)", pointerEvents: "none", fontSize: "1rem" }}>🔍</span>
        <input
          type="search"
          placeholder="İsme göre ara…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ paddingLeft: "2.4rem" }}
        />
      </div>

      {loading && (
        <div className="empty">
          <div style={{ width: 30, height: 30, border: "3px solid var(--border)", borderTopColor: "var(--teal)", borderRadius: "50%", animation: "spin .7s linear infinite", margin: "0 auto 1rem" }} />
          Yükleniyor…
        </div>
      )}

      {error && <div className="card" style={{ color: "var(--danger)" }}>Hata: {error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div style={{ textAlign: "center", padding: "4rem 2rem", background: "var(--white)", borderRadius: "var(--radius)", border: "1px solid var(--border)" }}>
          <div style={{ fontSize: "3.5rem", marginBottom: "1rem", opacity: .25 }}>🐢</div>
          {search
            ? <><p style={{ fontWeight: 700, marginBottom: ".4rem" }}>"{search}" için sonuç yok</p><p style={{ color: "var(--muted)", fontSize: ".9rem" }}>Farklı bir isim deneyin.</p></>
            : <><p style={{ fontWeight: 700, marginBottom: ".4rem" }}>Henüz kayıt yok</p>
                <p style={{ color: "var(--muted)", fontSize: ".9rem", marginBottom: "1.25rem" }}>İlk kaplumbağayı ekleyin.</p>
                <Link to="/turtles/new" className="btn-primary" style={{ display: "inline-block" }}>İlk kaydı oluştur</Link></>
          }
        </div>
      )}

      <div className="grid-3">
        {filtered.map((t) => (
          <div key={t.id} onClick={() => navigate(`/turtles/${t.id}`)} style={{ background: "var(--white)", border: "1px solid var(--border)", borderRadius: 16, padding: "1.4rem", display: "flex", flexDirection: "column", gap: ".9rem", cursor: "pointer", transition: "all .18s", boxShadow: "var(--shadow)" }}
            onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.boxShadow = "var(--shadow-md)"; e.currentTarget.style.borderColor = "var(--teal)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = "var(--shadow)"; e.currentTarget.style.borderColor = "var(--border)"; }}>
            <div style={{ width: 52, height: 52, borderRadius: "50%", background: color(t.name), display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.3rem", fontWeight: 900, color: "#fff", boxShadow: `0 4px 12px ${color(t.name)}55` }}>
              {t.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: "1.05rem", color: "var(--ink)", marginBottom: ".2rem" }}>{t.name}</div>
              {t.notes && <div style={{ fontSize: ".82rem", color: "var(--muted)", fontStyle: "italic", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginBottom: ".3rem" }}>{t.notes}</div>}
              <div style={{ fontSize: ".75rem", color: "var(--muted)" }}>
                {new Date(t.registered_at).toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" })}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
