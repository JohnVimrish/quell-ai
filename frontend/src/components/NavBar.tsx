import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "./AuthProvider";

type NavItem =
  | { type: "link"; to: string; label: string }
  | { type: "external"; href: string; label: string }
  | { type: "button"; action: "engage" | "logout"; label: string }
  | { type: "dropdown"; id: string; label: string; options: DropdownOption[] };

type DropdownOption = {
  to: string;
  label: string;
  onSelect?: () => void;
};

function Dropdown({
  item,
  isActive,
  isOpen,
  currentPath,
  onToggle,
  onOpen,
  onClose,
  onSelect,
}: {
  item: Extract<NavItem, { type: "dropdown" }>;
  isActive: boolean;
  isOpen: boolean;
  currentPath: string;
  onToggle: (id: string) => void;
  onOpen: (id: string) => void;
  onClose: () => void;
  onSelect: (option: DropdownOption) => void;
}) {
  return (
    <div
      className={`nav-dropdown nav-dropdown-${item.id} ${isOpen ? "nav-dropdown-open" : ""}`}
      onMouseLeave={onClose}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node)) {
          onClose();
        }
      }}
    >
      <button
        type="button"
        className={`nav-pill nav-dropdown-trigger ${isActive ? "nav-pill-active" : ""}`}
        aria-haspopup="true"
        aria-expanded={isOpen}
        onClick={() => onToggle(item.id)}
        onMouseEnter={() => onOpen(item.id)}
        onFocus={() => onOpen(item.id)}
      >
        <span>{item.label}</span>
        <span className="nav-dropdown-caret" aria-hidden="true">▾</span>
      </button>
      <div className="nav-dropdown-menu" role="menu">
        {item.options.map((option) => {
          const optionActive = option.to === currentPath;
          return (
            <button
              key={option.to}
              type="button"
              className={`nav-dropdown-option ${optionActive ? "nav-dropdown-option-active" : ""}`}
              role="menuitem"
              onClick={() => onSelect(option)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function NavBar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { isAuthed, isEngaged, engage, logout, backToAbout } = useAuth();
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [loginActive, setLoginActive] = useState(false);

  const navItems = useMemo<NavItem[]>(() => ([
    { type: "link", to: "/", label: "About" },
    { type: "link", to: "/labs/dev-playground", label: "Conversation Lab" },
  ]), []);

  useEffect(() => {
    setOpenDropdown(null);
    setLoginActive(false);
  }, [pathname]);

  const handleDropdownSelect = useCallback((option: DropdownOption) => {
    if (option.onSelect) {
      option.onSelect();
    } else if (option.to !== pathname) {
      navigate(option.to);
    }
    setOpenDropdown(null);
  }, [navigate, pathname]);

  const showBackToAbout = isEngaged && pathname !== "/";
  const showBrand = pathname === "/";

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
      <div className="brand" aria-label={showBrand ? "Quell AI" : undefined} aria-hidden={showBrand ? undefined : "true"}>
        <span>Quell AI</span>
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
                  `nav-pill nav-3d ${isActive ? "active-nav" : ""}`
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

          if (item.type === "dropdown") {
            const isActive = item.options.some((option) => option.to === pathname);
            const isOpen = openDropdown === item.id;
            return (
              <Dropdown
                key={item.id}
                item={item}
                isActive={isActive}
                isOpen={isOpen}
                currentPath={pathname}
                onToggle={(id) => setOpenDropdown((prev) => (prev === id ? null : id))}
                onOpen={(id) => setOpenDropdown(id)}
                onClose={() => setOpenDropdown((prev) => (prev === item.id ? null : prev))}
                onSelect={handleDropdownSelect}
              />
            );
          }

          if (item.type === "external") {
            return (
              <a key={item.href} href={item.href} className="nav-pill nav-3d nav-pill-outline">
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
      <button
        id="loginBtn"
        type="button"
        className={`nav-pill btn-3d ${loginActive ? "active-nav" : ""}`.trim()}
        onClick={() => {
          setLoginActive((prev) => !prev);
          navigate("/login");
        }}
        aria-pressed={loginActive}
      >
        Log In
      </button>
    </header>
  );
}


