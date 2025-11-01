import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import FloatingOrbs from "../components/FloatingOrbs";
import FlipbookViewer from "../components/FlipbookViewer";
import { ensurePublicTheme } from "../utils/publicTheme";
import { useAuth } from "../components/AuthProvider";

type NavId = "about" | "lab";

const FLIPBOOK_DOCUMENT_PATH = "/static/documents/quell_ai_interactive.pdf";

const FOOTER_COLUMNS = [
  {
    heading: "Institution",
    links: ["About", "Research Faculty"],
  },
  {
    heading: "Resources",
    links: ["Codex Chapters", "Methodologies", "Datasets"],
  },
  {
    heading: "Legal Framework",
    links: ["Privacy Policies", "Terms of Use"],
  },
];

function classNames(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export default function LandingPage() {
  const { engage } = useAuth();
  const navigate = useNavigate();
  const [activeNav, setActiveNav] = useState<NavId>("about");
  const [flipbookReady, setFlipbookReady] = useState(false);
  const [flipbookError, setFlipbookError] = useState<Error | null>(null);

  useEffect(() => {
    ensurePublicTheme();
  }, []);

  const handleNavClick = (target: NavId) => {
    setActiveNav(target);
    if (target === "about") {
      navigate("/");
    } else {
      navigate("/labs/dev-playground");
    }
  };

  const renderFlipbookOverlay = () => {
    if (flipbookError) {
      return (
        <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center px-4">
          <div className="mx-auto flex w-full max-w-3xl flex-col items-center justify-center rounded-2xl border border-red-200/80 bg-red-50/85 p-12 text-center shadow-xl shadow-red-200/30 backdrop-blur">
            <span className="text-lg font-semibold text-red-700">Unable to load the interactive codex.</span>
            <span className="mt-3 text-sm text-red-600">
              {flipbookError.message}
            </span>
          </div>
        </div>
      );
    }

    if (!flipbookReady) {
      return (
        <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center px-4">
          <div className="mx-auto flex w-full max-w-3xl flex-col items-center justify-center rounded-2xl border border-border-grey/70 bg-white/80 p-12 text-center shadow-xl shadow-primary-blue/20 backdrop-blur">
            <span className="text-lg font-semibold text-dark-text">Preparing the interactive codex.</span>
            <span className="mt-2 text-sm text-light-text">Rendering pages from the PDF document.</span>
            <span className="mt-6 h-1.5 w-40 animate-pulse rounded-full bg-primary-blue/60" />
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="bg-light-background font-sans text-dark-text antialiased">
      <div className="relative min-h-screen w-full overflow-x-hidden">
        <FloatingOrbs />

        <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <header className="sticky top-6 z-50 mt-6 grid h-16 grid-cols-3 items-center rounded-lg border border-border-grey bg-light-background/90 px-4 shadow-md backdrop-blur-md sm:px-6">
            <div className="flex items-center gap-3 justify-self-start">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary-blue/10 text-primary-blue">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" fill="currentColor" />
                </svg>
              </div>
              <span className="hidden text-xl font-bold text-dark-text sm:block">Quell AI</span>
            </div>
            <nav className="hidden items-center justify-center gap-2 justify-self-center md:flex">
              <button
                type="button"
                className={classNames(
                  "nav-3d rounded-md px-4 py-2 text-sm font-semibold text-light-text transition-all hover:bg-primary-blue/10 hover:text-primary-blue focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50",
                  activeNav === "about" && "active-nav",
                )}
                aria-current={activeNav === "about" ? "page" : undefined}
                onClick={() => handleNavClick("about")}
              >
                About
              </button>
              <button
                type="button"
                className={classNames(
                  "nav-3d rounded-md px-4 py-2 text-sm font-semibold text-light-text transition-all hover:bg-primary-blue/10 hover:text-primary-blue focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50",
                  activeNav === "lab" && "active-nav",
                )}
                aria-current={activeNav === "lab" ? "page" : undefined}
                onClick={() => handleNavClick("lab")}
              >
                Conversation Lab
              </button>
            </nav>
            <div className="flex items-center gap-3 justify-self-end">
              <button
                type="button"
                className="btn-3d hidden h-10 cursor-pointer items-center justify-center rounded-md border border-primary-blue/30 bg-white/80 px-5 text-sm font-bold text-dark-text shadow-lg hover:bg-primary-blue/10 hover:text-primary-blue sm:flex"
                onClick={() => navigate("/login")}
              >
                Log In
              </button>
              <button
                type="button"
                className="flex h-10 min-w-[108px] cursor-pointer items-center justify-center overflow-hidden rounded-md border border-primary-blue/30 bg-primary-blue px-5 text-sm font-bold text-white shadow-lg shadow-primary-blue/20 transition-all hover:scale-105 hover:bg-hover-blue"
                onClick={() => engage()}
              >
                Access Portal
              </button>
            </div>
          </header>

          <main className="flex flex-col">
            <section
              id="about"
              className="relative flex min-h-[calc(100vh-120px)] flex-col items-center justify-center pt-6 pb-16 text-center"
            >
              <div className="relative z-10 w-full max-w-5xl rounded-xl border border-border-grey bg-white/80 p-8 shadow-xl backdrop-blur-md sm:p-12 md:p-16">
                <div className="flex flex-col items-center gap-6">
                  <h1 className="max-w-4xl font-serif text-5xl font-bold leading-tight tracking-tight text-dark-text md:text-6xl">
                    Deep Dive into Natural Language Processing.
                  </h1>
                  <p className="max-w-2xl text-lg text-light-text">
                    A comprehensive codex for scholars and researchers exploring the multifaceted capabilities of NLP.
                  </p>
                  <button
                    className="mt-4 flex h-12 min-w-[84px] cursor-pointer items-center justify-center overflow-hidden rounded-md border border-primary-blue/30 bg-primary-blue px-6 text-base font-bold text-white shadow-lg shadow-primary-blue/20 transition-all hover:scale-105 hover:bg-hover-blue"
                    onClick={() => engage()}
                  >
                    Explore the Codex
                  </button>
                </div>
              </div>
            </section>

            <section className="relative w-full pb-24" style={{ marginTop: "2in" }}>
              <div className="relative mx-auto w-full max-w-6xl">
                {renderFlipbookOverlay()}
                <FlipbookViewer
                  pdfUrl={FLIPBOOK_DOCUMENT_PATH}
                  className="relative z-10"
                  onLoading={() => {
                    setFlipbookReady(false);
                    setFlipbookError(null);
                  }}
                  onReady={() => setFlipbookReady(true)}
                  onError={(error) => {
                    setFlipbookReady(false);
                    setFlipbookError(error);
                  }}
                />
              </div>
            </section>
          </main>

          <footer className="relative z-10 mx-auto mt-20 max-w-7xl border-t border-border-grey bg-light-background/90 px-4 py-10 text-center backdrop-blur-sm sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 gap-8 text-left md:grid-cols-4">
              {FOOTER_COLUMNS.map((column) => (
                <div key={column.heading}>
                  <h4 className="font-bold text-dark-text">{column.heading}</h4>
                  <ul className="mt-4 space-y-2">
                    {column.links.map((link) => (
                      <li key={link}>
                        <a className="text-sm text-light-text hover:text-dark-text" href="#">
                          {link}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              <div>
                <h4 className="font-bold text-dark-text">Connect</h4>
                <div className="mt-4 flex gap-4">
                  <a className="text-light-text hover:text-dark-text" href="#" aria-label="Twitter">
                    <svg aria-hidden="true" className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.71v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path>
                    </svg>
                  </a>
                  <a className="text-light-text hover:text-dark-text" href="#" aria-label="LinkedIn">
                    <svg aria-hidden="true" className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                      <path clipRule="evenodd" d="M16.338 16.338H13.67V12.16c0-.995-.017-2.277-1.387-2.277-1.39 0-1.601 1.086-1.601 2.206v4.248H8.014v-8.59h2.559v1.174h.037c.356-.675 1.225-1.387 2.526-1.387 2.703 0 3.203 1.778 3.203 4.092v4.711zM5.005 6.575a1.548 1.548 0 11-.003-3.096 1.548 1.548 0 01.003 3.096zm-1.47 1.344h2.94v8.59H3.535v-8.59z" fillRule="evenodd"></path>
                    </svg>
                  </a>
                </div>
              </div>
            </div>
            <div className="mt-10 border-t border-border-grey pt-6">
              <p className="text-sm text-light-text">&copy; 2024 CogniLex Codex. All Rights Reserved.</p>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}
