import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useMemo } from "react";

type NavItem = { to: string; label: string; exact?: boolean };
type CtaConfig = { to: string; label: string; highlight: boolean };

type NavConfig = {
  navItems: NavItem[];
  cta: CtaConfig;
};

export default function NavBar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  const config = useMemo<NavConfig>(() => {
    if (pathname.startsWith("/login")) {
      return {
        navItems: [
          { to: "/", label: "About", exact: true },
          { to: "/signup", label: "Create Account" },
        ],
        cta: { to: "/login", label: "Sign In", highlight: true },
      };
    }

    if (pathname.startsWith("/signup")) {
      return {
        navItems: [
          { to: "/", label: "About", exact: true },
          { to: "/signup", label: "Create Account" },
        ],
        cta: { to: "/login", label: "Sign In", highlight: false },
      };
    }

    return {
      navItems: [
        { to: "/", label: "About", exact: true },
        { to: "/labs/conversation-lab", label: "Conversation Lab" },
        { to: "/login", label: "Login" },
      ],
      cta: { to: "/signup", label: "Create Account", highlight: pathname.startsWith("/signup") },
    };
  }, [pathname]);

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <header className="sticky top-6 z-50 mt-6 grid h-16 grid-cols-3 items-center rounded-lg border border-border-grey bg-light-background/90 px-4 shadow-md backdrop-blur-md sm:px-6">
        <div className="flex items-center gap-3 justify-self-start">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary-blue/10 text-primary-blue">
            <svg className="h-6 w-6" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" fill="currentColor" />
            </svg>
          </div>
          <button type="button" className="hidden text-xl font-bold text-dark-text sm:block" onClick={() => navigate("/")}>
            Quell AI
          </button>
        </div>
        <nav className="hidden md:flex items-center gap-2 justify-center justify-self-center">
          {config.navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact === true}
              className={({ isActive }) =>
                `nav-3d rounded-md px-4 py-2 text-sm font-semibold text-light-text transition-all hover:bg-primary-blue/10 hover:text-primary-blue focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50 ${
                  isActive ? "active-nav" : ""
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-3 justify-self-end">
          <button
            type="button"
            className={`btn-3d hidden h-10 cursor-pointer items-center justify-center rounded-md border border-primary-blue/30 bg-white/80 px-5 text-sm font-bold text-dark-text shadow-lg hover:bg-primary-blue/10 hover:text-primary-blue sm:flex ${
              config.cta.highlight ? "active-nav" : ""
            }`}
            onClick={() => navigate(config.cta.to)}
          >
            {config.cta.label}
          </button>
        </div>
      </header>
    </div>
  );
}
