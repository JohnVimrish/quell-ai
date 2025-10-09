import { NavLink } from "react-router-dom";
import { useAuth } from "./AuthProvider";

const fullRoutes = [
  { to: "/", label: "About" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/calls", label: "Calls" },
  { to: "/contacts", label: "Contacts" },
  { to: "/texts", label: "Texts" },
  { to: "/reports", label: "Reports" },
  { to: "/settings", label: "Settings" },
];

export default function NavBar() {
  const { isAuthed, experience, logout } = useAuth();

  return (
    <header className="navbar" data-ui="navbar">
      <div className="brand"><span>Quell-AI</span></div>
      <nav className={`nav-links ${!isAuthed ? 'nav-centered' : ''}`}>
        {!isAuthed && (
          <>
            <NavLink to="/" className={({ isActive }) => (isActive ? "active" : undefined)}>About</NavLink>
            <button 
              className="button-engage" 
              onClick={(e) => {
                e.currentTarget.classList.add('is-engaged');
                experience();
              }}
            >
              Engage with the Application
            </button>
            <NavLink className="button-outline" to="/login">Log in</NavLink>
          </>
        )}
        {isAuthed && (
          <>
            {fullRoutes.map(({ to, label }) => (
              <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "active" : undefined)}>
                {label}
              </NavLink>
            ))}
            <button className="button-outline" onClick={logout}>Log out</button>
          </>
        )}
      </nav>
    </header>
  );
}
