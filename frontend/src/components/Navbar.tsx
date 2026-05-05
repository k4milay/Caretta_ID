import { NavLink } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-brand">
          <div className="navbar-logo">🐢</div>
          <span className="navbar-wordmark">CarettaID</span>
        </NavLink>
        <div className="navbar-links">
          <NavLink to="/" end className={({ isActive }) => isActive ? "active" : ""}>
            Sorgula
          </NavLink>
          <NavLink to="/turtles" className={({ isActive }) => isActive ? "active" : ""}>
            Kaplumbağalar
          </NavLink>
          <NavLink to="/turtles/new" className="nav-cta">
            + Yeni Kayıt
          </NavLink>
        </div>
      </div>
    </nav>
  );
}
