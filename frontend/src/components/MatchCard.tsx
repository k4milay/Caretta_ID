import { Link } from "react-router-dom";
import type { MatchResult } from "../services/api";

interface Props { match: MatchResult; rank: number; }

export default function MatchCard({ match, rank }: Props) {
  const pct = (match.similarity_score * 100).toFixed(1);

  return (
    <div className="card match-card">
      <div className="match-rank">#{rank}</div>
      <Link to={`/turtles/${match.turtle_id}`} className="match-name">
        {match.name}
      </Link>
      <div className="match-score">
        <div className="score-bar-bg">
          <div className="score-bar-fill" style={{ width: `${pct}%` }} />
        </div>
        <span>{pct}%</span>
      </div>
      <span className={`badge badge-${match.confidence}`}>
        {match.confidence === "high" ? "Yüksek" : match.confidence === "medium" ? "Orta" : "Düşük"} Güven
      </span>
    </div>
  );
}
