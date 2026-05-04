import { NavLink } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className="navbar-brand">
        🐢 CarettaID
      </NavLink>
      <div className="navbar-links">
        <NavLink to="/"        end className={({ isActive }) => isActive ? "active" : ""}>Tanımla</NavLink>
        <NavLink to="/turtles"     className={({ isActive }) => isActive ? "active" : ""}>Kaplumbağalar</NavLink>
        <NavLink to="/turtles/new" className="btn-primary" style={{ padding: ".4rem .9rem", borderRadius: 6 }}>+ Yeni Kayıt</NavLink>
      </div>
    </nav>
  );
}
