import { NavLink, useLocation } from "react-router-dom";
import { useMemo } from "react";
import { useAuth } from "./AuthProvider";

type NavItem =
  | { type: "link"; to: string; label: string }
  | { type: "external"; href: string; label: string }
  | { type: "button"; action: "engage" | "logout"; label: string };

export default function NavBar() {
  const { pathname } = useLocation();
  const { isAuthed, isEngaged, engage, logout, backToAbout } = useAuth();

  const navItems = useMemo<NavItem[]>(() => {
    if (isAuthed) {
      return [
        { type: "link", to: "/dashboard", label: "Dashboard" },
        { type: "link", to: "/calls", label: "Calls" },
        { type: "link", to: "/contacts", label: "Contacts" },
        { type: "link", to: "/texts", label: "Texts" },
        { type: "link", to: "/reports", label: "Reports" },
        { type: "link", to: "/settings", label: "Settings" },
        { type: "button", action: "logout", label: "Log out" },
      ];
    }

    if (isEngaged) {
      return [
        { type: "link", to: "/", label: "About" },
        { type: "link", to: "/why", label: "Why Quell-AI" },
        { type: "link", to: "/dashboard", label: "Dashboard" },
        { type: "link", to: "/calls", label: "Calls" },
        { type: "link", to: "/contacts", label: "Contacts" },
        { type: "link", to: "/texts", label: "Texts" },
        { type: "link", to: "/reports", label: "Reports" },
        { type: "link", to: "/labs/message-understanding", label: "Message Lab" },
      ];
    }

    return [
      { type: "link", to: "/", label: "About" },
      { type: "button", action: "engage", label: "Engage with the Application" },
      { type: "external", href: "/legacy/login.html", label: "Log in" },
    ];
  }, [isAuthed, isEngaged]);

  const showBackToAbout = isEngaged && pathname !== "/";

  return (
    <header className={`navbar ${isEngaged || isAuthed ? "navbar-expanded" : ""}`} data-ui="navbar">
      {showBackToAbout && (
        <button
          className="nav-back-button"
          onClick={backToAbout}
          type="button"
        >
          Back to About
        </button>
      )}
      <div className="brand" aria-label="Quell-AI">
        <span>Quell-AI</span>
      </div>
      <nav className={`nav-links ${!isAuthed && !isEngaged ? "nav-centered" : "nav-expanded"}`}>
        {navItems.map((item) => {
          if (item.type === "link") {
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `nav-pill ${isActive ? "nav-pill-active" : ""}`
                }
                onClick={() => {
                  if (item.to === "/") {
                    backToAbout();
                  }
                }}
              >
                {item.label}
              </NavLink>
            );
          }

          if (item.type === "external") {
            return (
              <a key={item.href} href={item.href} className="nav-pill nav-pill-outline">
                {item.label}
              </a>
            );
          }

          const extraClasses =
            item.action === "engage"
              ? isEngaged
                ? "nav-pill-active"
                : ""
              : item.action === "logout"
                ? "nav-pill-outline"
                : "";

          return (
            <button
              key={item.action}
              type="button"
              className={`nav-pill nav-pill-button ${extraClasses}`.trim()}
              onClick={() => {
                if (item.action === "engage") {
                  engage();
                } else if (item.action === "logout") {
                  logout();
                }
              }}
            >
              {item.label}
            </button>
          );
        })}
      </nav>
      {/* Keep layout balance */}
      <div className="nav-spacer" aria-hidden="true" />
    </header>
  );
}
