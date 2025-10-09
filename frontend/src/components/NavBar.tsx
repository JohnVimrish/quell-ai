import { NavLink } from "react-router-dom";

const routes = [
  { to: "/", label: "About" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/features", label: "Product" },
  { to: "/pricing", label: "Pricing" },
  { to: "/faq", label: "FAQs" },
  { to: "/contact", label: "Contact" },
];

export default function NavBar() {
  return (
    <header className="navbar" data-ui="navbar">
      <div className="brand">Quell-AI</div>
      <nav className="nav-links">
        {routes.map(({ to, label }) => (
          <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "active" : undefined)}>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="auth-links">
        <NavLink className="button-primary" to="/login">
          Login
        </NavLink>
        <NavLink className="button-primary button-secondary" to="/register">
          Sign Up
        </NavLink>
      </div>
    </header>
  );
}
