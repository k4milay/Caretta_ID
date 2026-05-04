import { useState } from "react";
import { Link } from "react-router-dom";
import DropZone from "../components/DropZone";
import MatchCard from "../components/MatchCard";
import "../components/MatchCard.css";
import { identifyApi, type IdentificationResponse } from "../services/api";

type State = "idle" | "loading" | "done" | "error";

export default function IdentifyPage() {
  const [file, setFile]           = useState<File | null>(null);
  const [state, setState]         = useState<State>("idle");
  const [result, setResult]       = useState<IdentificationResponse | null>(null);
  const [errorMsg, setErrorMsg]   = useState("");
  const [topK, setTopK]           = useState(5);
  const [threshold, setThreshold] = useState(0.60);

  async function handleIdentify() {
    if (!file) return;
    setState("loading");
    setResult(null);
    try {
      const res = await identifyApi.identify(file, "head", topK);
      setResult(res);
      setState("done");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Bir hata oluştu.");
      setState("error");
    }
  }

  return (
    <div className="page">
      <h1 className="page-title">🔍 Kaplumbağa Tanımlama</h1>

      <div className="grid-2" style={{ gap: "1.5rem" }}>
        {/* Left — upload + controls */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <DropZone onFile={setFile} />

          <div className="card" style={{ display: "flex", flexDirection: "column", gap: ".75rem" }}>
            <div>
              <label>Sonuç sayısı (top-K): {topK}</label>
              <input type="range" min={1} max={10} value={topK}
                onChange={(e) => setTopK(Number(e.target.value))} />
            </div>
            <div>
              <label>Eşik: %{(threshold * 100).toFixed(0)}</label>
              <input type="range" min={0.5} max={1.0} step={0.01} value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))} />
            </div>
            <button
              className="btn-primary"
              disabled={!file || state === "loading"}
              onClick={handleIdentify}
            >
              {state === "loading" ? "Analiz ediliyor…" : "Tanımla"}
            </button>
          </div>
        </div>

        {/* Right — results */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {state === "idle" && (
            <div className="card empty">Fotoğraf yükleyip <b>Tanımla</b> butonuna basın.</div>
          )}

          {state === "loading" && (
            <div className="card empty">⏳ Model çalışıyor…</div>
          )}

          {state === "error" && (
            <div className="card" style={{ color: "var(--danger)" }}>❌ {errorMsg}</div>
          )}

          {state === "done" && result && (
            <>
              <div className="card" style={{ fontWeight: 600 }}>
                {result.accepted
                  ? `✅ ${result.matches.length} eşleşme bulundu`
                  : "❌ Eşleşme yok — bu kaplumbağa daha önce kayıt edilmemiş olabilir"}
              </div>

              {result.matches.map((m, i) => (
                <MatchCard key={m.turtle_id} match={m} rank={i + 1} />
              ))}

              {!result.accepted && (
                <Link to="/turtles/new" className="btn-primary" style={{ display: "block", textAlign: "center", padding: ".6rem" }}>
                  + Yeni Kaplumbağa Olarak Kaydet
                </Link>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
