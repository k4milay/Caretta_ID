import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { turtleApi, type Turtle } from "../services/api";

export default function TurtleListPage() {
  const [turtles, setTurtles]   = useState<Turtle[]>([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState("");
  const [error, setError]       = useState("");

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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>🐢 Kayıtlı Kaplumbağalar</h1>
        <Link to="/turtles/new" className="btn-primary">+ Yeni Kayıt</Link>
      </div>

      <input
        type="search"
        placeholder="İsme göre ara…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ marginBottom: "1rem" }}
      />

      {loading && <div className="empty">Yükleniyor…</div>}
      {error   && <div className="card" style={{ color: "var(--danger)" }}>❌ {error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div className="empty">
          {search ? "Arama sonucu bulunamadı." : "Henüz kayıtlı kaplumbağa yok."}
          {!search && <><br /><Link to="/turtles/new">İlk kaydı oluştur →</Link></>}
        </div>
      )}

      <div className="grid-3">
        {filtered.map((t) => (
          <Link key={t.id} to={`/turtles/${t.id}`} style={{ textDecoration: "none" }}>
            <div className="card turtle-card">
              <div className="turtle-avatar">🐢</div>
              <div className="turtle-name">{t.name}</div>
              <div className="turtle-meta">
                {new Date(t.registered_at).toLocaleDateString("tr-TR")} tarihinde kayıt edildi
              </div>
              {t.notes && <div className="turtle-notes">{t.notes}</div>}
            </div>
          </Link>
        ))}
      </div>

      <style>{`
        .turtle-card { display:flex; flex-direction:column; gap:.4rem; transition:transform .15s; }
        .turtle-card:hover { transform:translateY(-2px); }
        .turtle-avatar { font-size:2rem; }
        .turtle-name { font-weight:700; font-size:1.05rem; color:var(--ink); }
        .turtle-meta { font-size:.78rem; color:var(--muted); }
        .turtle-notes { font-size:.82rem; color:var(--muted); font-style:italic; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      `}</style>
    </div>
  );
}
