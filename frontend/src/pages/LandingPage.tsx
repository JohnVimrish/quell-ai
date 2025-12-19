import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import FloatingOrbs from "../components/FloatingOrbs";
import FlipbookViewer from "../components/FlipbookViewer";
import NavBar from "../components/NavBar";
import { ensurePublicTheme } from "../utils/publicTheme";
import "./LandingPage.css";
import usePrefersReducedMotion from "../hooks/usePrefersReducedMotion";
import useRevealOnIntersect from "../hooks/useRevealOnIntersect";
import heroIllustration from "../assets/images/relax_picture.png";
import storyboardChaos from "../assets/images/worry_picture.png";
import storyboardIdea from "../assets/images/solution_address_picture.png";
import storyboardSupport from "../assets/images/relax_picture.png";

const FLIPBOOK_DOCUMENT_PATH = "/static/documents/quell_ai_interactive.pdf";

const FOOTER_SECTIONS = [
  {
    heading: "Pages",
    links: [
      // About should always point to the Landing page
      { label: "About", href: "/" },
    ],
  },
  {
    heading: "Resources",
    links: [
      // Both lab links route to Conversation Lab
      { label: "ChatLab", href: "/labs/conversation-lab" },
      { label: "VoiceLab", href: "/labs/conversation-lab" },
    ],
  },
];

const SCENARIO_ROWS = [
  {
    before: [
      "Developers often spend two or three hours a day responding to status messages and attending check-ins that break focus.",
      "Important updates get buried in endless notifications, and meaningful creative flow is lost in the noise.",
    ],
    after: [
      "Quell AI joins calls or threads on your behalf, listens, and creates clear, concise summaries.",
      "It distills only what matters: key decisions, blockers, and next actions, allowing teams to stay informed without sacrificing productivity.",
    ],
  },
  {
    before: [
      "Knowledge tends to scatter across documents, chats, and dashboards, making it difficult to retrieve when it is most needed.",
      "Teams waste time searching for context or recreating already existing information.",
    ],
    after: [
      "Quell AI keeps a continuous record of relevant knowledge within your authorized ecosystem.",
      "When context is requested, whether in a chat, meeting, or email, it provides instant, precise answers derived from approved sources.",
    ],
  },
  {
    before: [
      "Team leads often feel overwhelmed managing multiple priorities, schedules, and communications.",
      "The mental overhead of coordination becomes a bottleneck to effective leadership.",
    ],
    after: [
      "Quell AI automates repetitive coordination by sending follow-ups, documenting outcomes, and highlighting actionable insights.",
      "This allows leaders to focus on strategy and human connection rather than constant information triage.",
    ],
  },
];

const NEEDS_POINTS = [
  {
    title: "Reduced Collaboration Fatigue",
    description:
      "When communication tools demand constant attention, focus suffers. Quell AI minimizes unnecessary noise by handling routine participation autonomously and aims to simplify collaboration rather than amplify complexity.",
  },
  {
    title: "Accelerated Understanding",
    description:
      "Instead of chasing updates across platforms, Quell AI ensures knowledge is surfaced instantly, allowing teams to move from alignment to action faster.",
  },
  {
    title: "Privacy by Design",
    description:
      "Every decision in Quell AI's architecture begins with user control and data minimization so your information remains yours.",
  },
  {
    title: "Built for the Modern Workforce",
    description:
      "Designed for hybrid, distributed teams, Quell AI brings context continuity regardless of time zone or presence.",
  },
];

const ROADMAP_PHASES = ["Phase 1: Meeting agent", "Phase 2: Knowledge concierge", "Phase 3: Team memory graph"];

const AGENT_BULLETS = [
  {
    title: "Bounded access",
    paragraphs: [
      "Quell AI operates strictly within the permissions you grant. Using directory or group-based scoping, it can only access content you explicitly allow.",
      "This balance between automation and trust ensures that your digital twin never sees more than you intend it to.",
    ],
  },
  {
    title: "Contextual answers",
    paragraphs: [
      "At its core, Quell AI leverages retrieval-augmented generation (RAG) to draw precise responses from your approved data.",
      "The agent stays relevant and context aware, so answers are not just accurate but situationally meaningful.",
    ],
  },
  {
    title: "Live presence",
    paragraphs: [
      "Quell AI can attend meetings, transcribe discussions, and summarize action items in real time.",
      "It bridges asynchronous and live collaboration by ensuring continuity so every conversation becomes searchable, referenceable knowledge.",
    ],
  },
  {
    title: "User control",
    paragraphs: [
      "You remain the ultimate authority. Every action can be reviewed or overridden, and meeting organizers can always choose human presence over automation.",
      "The AI assists; it never replaces human intent or accountability.",
    ],
  },
];

function classNames(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export default function LandingPage() {
  const navigate = useNavigate();
  const [flipbookReady, setFlipbookReady] = useState(false);
  const [flipbookError, setFlipbookError] = useState<Error | null>(null);
  const [activeProposalButton, setActiveProposalButton] = useState<"hero" | "vision" | null>(null);
  const prefersReducedMotion = usePrefersReducedMotion();
  const codexSectionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    ensurePublicTheme();
  }, []);

  const handleScrollToCodex = (source: "hero" | "vision") => {
    const node = codexSectionRef.current;
    if (!node) return;
    setActiveProposalButton(source);
    node.scrollIntoView({
      behavior: prefersReducedMotion ? "auto" : "smooth",
      block: "start",
    });
  };

  const handleJoinBeta = () => {
    navigate("/signup");
  };

  const renderFlipbookOverlay = () => {
    if (flipbookError) {
      return (
        <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center px-4">
          <div className="mx-auto flex w-full max-w-3xl flex-col items-center justify-center rounded-2xl border border-red-200/80 bg-red-50/85 p-12 text-center shadow-xl shadow-red-200/30 backdrop-blur">
            <span className="text-lg font-semibold text-red-700">Unable to load the interactive codex.</span>
            <span className="mt-3 text-sm text-red-600">{flipbookError.message}</span>
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
          <NavBar />
          <main className="snap-container flex flex-col">
            <section
              id="about"
              className="snap-section relative flex min-h-[calc(100vh-120px)] flex-col items-center justify-center pt-6 pb-16 text-center"
            >
              <div className="hero-shell relative z-10 w-full max-w-6xl overflow-hidden rounded-[40px] border border-primary-blue/20 bg-white/85 p-10 text-left shadow-xl shadow-primary-blue/20 backdrop-blur-lg sm:px-14 md:px-16 md:py-14">
                <div className="grid gap-10 md:grid-cols-[minmax(0,0.95fr)_minmax(0,0.75fr)] md:items-center">
                  <div className="flex flex-col gap-6">
                    <span className="text-xs font-semibold uppercase tracking-[0.4em] text-primary-blue/70">Proposal Preview</span>
                    <h1 className="font-serif text-4xl font-bold leading-tight text-dark-text md:text-5xl lg:text-6xl">
                      Quell AI: Rethinking Collaboration Through Intelligent Presence
                    </h1>
                    <div className="space-y-4 text-base text-light-text md:text-lg">
                      <p>
                        In an age of constant pings, overlapping meetings, and fragmented communication, Quell AI proposes a new way forward. It is not a product yet; it is a vision.
                      </p>
                      <p>
                        The concept imagines a collaboration agent that represents you intelligently when you cannot be there, maintaining context, capturing intent, and helping teams stay in sync without adding more noise.
                      </p>
                    </div>
                    <div
                      className={classNames(
                        "hero-keywords mt-4 flex flex-wrap items-center gap-3 text-sm font-semibold uppercase tracking-[0.35em] text-primary-blue",
                        prefersReducedMotion && "hero-keywords--static",
                      )}
                    >
                      {["Collaboration", "Context", "Continuity"].map((word, index) => (
                        <span key={word} className="hero-keyword" style={{ animationDelay: `${index * 1.6}s` }}>
                          {word}
                        </span>
                      ))}
                    </div>
                    <button
                      className={classNames(
                        "proposal-button mt-6 inline-flex h-12 min-w-[160px] items-center justify-center overflow-hidden rounded-full border border-primary-blue/30 bg-primary-blue px-7 text-sm font-bold text-white shadow-lg shadow-primary-blue/25 transition-all hover:scale-105 hover:bg-hover-blue focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/60",
                        activeProposalButton === "hero" && "button-active",
                      )}
                      onClick={() => handleScrollToCodex("hero")}
                    >
                      View Proposal
                    </button>
                  </div>
                  <figure className="hero-figure relative flex justify-center">
                    <img
                      src={heroIllustration}
                      alt="Concept illustration depicting an AI assistant supporting a focused professional"
                      loading="lazy"
                      decoding="async"
                      className={classNames("hero-illustration w-full max-w-md rounded-[32px] border border-primary-blue/15 shadow-xl", prefersReducedMotion && "hero-illustration--static")}
                    />
                    <figcaption className="sr-only">
                      Concept illustration showing Quell AI as an intelligent presence that protects focus.
                    </figcaption>
                  </figure>
                </div>
              </div>
            </section>

            <div className="flex flex-col gap-24 pb-24 md:gap-28">
              <WhySection />
              <OriginSection />
              <ScenariosSection />
              <WhyTeamsNeedSection />
              <AgentSection />
              <WhyItMattersSection />
              <VisionSection activeProposalButton={activeProposalButton} onExploreCodex={handleScrollToCodex} onJoinBeta={handleJoinBeta} />

              <section id="codex" ref={codexSectionRef} className="relative w-full">
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
            </div>
          </main>

          <footer className="relative z-10 mx-auto mt-20 max-w-7xl border-t border-border-grey bg-light-background/90 px-4 py-10 text-center backdrop-blur-sm sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 gap-8 text-left md:grid-cols-3">
              {FOOTER_SECTIONS.map((section) => (
                <div key={section.heading}>
                  <h4 className="font-bold text-dark-text">{section.heading}</h4>
                  <ul className="mt-4 space-y-2">
                    {section.links.map((link) => (
                      <li key={link.label}>
                        <button
                          type="button"
                          className="text-left text-sm text-light-text hover:text-dark-text"
                          onClick={() => navigate(link.href)}
                        >
                          {link.label}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              <div>
                <h4 className="font-bold text-dark-text">Connect</h4>
                <div className="mt-4 flex gap-4">
                  <a
                    className="footer-linkedin"
                    href="https://www.linkedin.com/in/john-vimrish/"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="LinkedIn"
                  >
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

function WhySection() {
  const sectionRef = useRevealOnIntersect<HTMLElement>();

  return (
    <section
      id="about-why"
      ref={sectionRef}
      className="reveal snap-section relative overflow-hidden rounded-[32px] border border-border-grey/60 bg-gradient-to-br from-white/95 via-white/85 to-primary-blue/10 px-6 py-16 shadow-xl shadow-primary-blue/15 backdrop-blur lg:px-16 lg:py-20"
      aria-labelledby="about-why-heading"
    >
      <div className="pointer-events-none absolute inset-0">
        <span
          className="about-float"
          style={{ width: "320px", height: "320px", top: "-120px", left: "-140px", background: "rgba(42, 58, 91, 0.4)" }}
          aria-hidden="true"
        />
        <span
          className="about-float about-float--secondary"
          style={{ width: "260px", height: "260px", bottom: "-110px", right: "-120px", background: "rgba(158, 191, 214, 0.45)" }}
          aria-hidden="true"
        />
        <span
          className="about-float about-float--tertiary"
          style={{ width: "220px", height: "220px", top: "40%", left: "25%", background: "rgba(90, 121, 181, 0.35)" }}
          aria-hidden="true"
        />
      </div>
      <div className="relative z-10 mx-auto flex max-w-3xl flex-col items-center gap-6 text-center">
        <p className="typewriter text-xs font-semibold uppercase tracking-[0.4em] text-primary-blue/70">
          Work is noisy. Focus is rare.
        </p>
        <h2 id="about-why-heading" className="max-w-2xl font-serif text-3xl font-bold text-dark-text md:text-4xl">
          Collaboration should feel calm, not chaotic.
        </h2>
        <div className="space-y-4 text-lg text-light-text md:text-xl">
          <p>
            Todayâ€™s workspaces are louder than ever, not with sound but with signals. Every notification demands attention, every platform promises connection, and every meeting adds another layer of complexity.
          </p>
          <p>
            Quell AI proposes a quieter, smarter form of collaboration where communication flows naturally and your focus remains untouched.
          </p>
          <p>
            By learning context, preserving intent, and acting only when needed, Quell AI turns digital chaos into cognitive calm. It empowers teams to collaborate intentionally instead of reactively.
          </p>
        </div>
        <div className="mt-4 flex flex-wrap justify-center gap-3 text-xs font-semibold uppercase tracking-[0.32em] text-primary-blue/70">
          <span>Intentional Collaboration</span>
          <span>Focus First</span>
          <span>Signals, not Noise</span>
        </div>
      </div>
    </section>
  );
}

function OriginSection() {
  const sectionRef = useRevealOnIntersect<HTMLElement>();
  const prefersReducedMotion = usePrefersReducedMotion();

    const originParagraphs = useMemo(
    () => [
      "In today’s connected world, collaboration is the heartbeat of productivity. Teams depend on constant communication through platforms such as Teams, Google Meet, and Zoom to align, share knowledge, and deliver results. Yet the same tools that enable connection can easily become a source of fatigue.",
      "Imagine a developer juggling several projects or a team lead managing multiple groups. Continuous meeting requests, follow-up emails, and overlapping conversations often disrupt focus and delay outcomes. When someone takes unplanned leave or faces an emergency, the flow of information breaks and others must document decisions, resend context, or request minutes after the fact.",
      "Many AI tools already translate languages, summarize meetings, or schedule sessions, but they solve isolated problems. What is missing is continuity: an AI that does not simply assist but can truly stand in for you.",
      "Quell AI addresses that gap. It is a proposal, not a finished product, outlining what intelligent collaboration could become. The concept envisions an agent or bot that can activate during your absence or whenever you choose, operating under strict, user-defined permissions.",
      "The agent would access only the data you authorize, scoped through your organization’s Active Directory groups. It could answer questions or provide information on your behalf using retrieval-augmented generation to deliver data-backed responses. It could join meetings in your place, recording, transcribing, and summarizing in real time, and even speak naturally in your voice when the required information is within reach.",
      "The goal is not to replace people but to help them stay connected, focused, and efficient even when real-time participation is impossible. From emergencies to time zone gaps between onshore and offshore teams, Quell AI’s vision bridges these divides and orchestrates collaboration responsibly.",
    ],
    [],
  );

    const storyboard = [
    {
      src: storyboardChaos,
      alt: "Illustration showing overwhelming notifications and communication overload",
      caption: "Every ping steals a moment of focus.",
    },
    {
      src: storyboardIdea,
      alt: "Illustration showing an AI aura forming around a workspace",
      caption: "Then came an idea: what if collaboration could think with you?",
    },
    {
      src: storyboardSupport,
      alt: "Illustration depicting an AI presence supporting calm, balanced work",
      caption: "When you cannot be there, your work still moves forward.",
    },
  ];

  return (
    <section
      id="about-origin"
      ref={sectionRef}
      className="reveal snap-section grid gap-12 rounded-[32px] border border-border-grey/60 bg-white/80 p-8 shadow-lg shadow-primary-blue/10 backdrop-blur md:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:p-14"
      aria-labelledby="about-origin-heading"
    >
      <div className="flex flex-col gap-5">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-primary-blue/70">Origin Story</p>
        <h2 id="about-origin-heading" className="font-serif text-3xl font-bold text-dark-text md:text-4xl">
          It began with a simple question: what if meetings could run themselves?
        </h2>
        <div className="space-y-4 text-base leading-relaxed text-light-text md:text-lg">
          {originParagraphs.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>
      </div>
      <div className="flex flex-col gap-6">
        {storyboard.map((frame, index) => (
          <figure
            key={frame.caption}
            className={classNames(
              "about-card relative overflow-hidden rounded-[28px] border border-primary-blue/20 bg-white/90 p-4 shadow-md shadow-primary-blue/15",
              "storyboard-frame",
            )}
            style={{ transitionDelay: `${index * 90}ms` }}
          >
            <img
              src={frame.src}
              alt={frame.alt}
              loading="lazy"
              decoding="async"
              className={classNames("storyboard-image w-full rounded-[22px] border border-primary-blue/15 object-cover", prefersReducedMotion && "storyboard-image--static")}
            />
            <figcaption className="mt-3 text-sm font-medium text-primary-blue/80">{frame.caption}</figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

function ScenariosSection() {
  const sectionRef = useRevealOnIntersect<HTMLElement>();

  return (
    <section
      id="about-scenarios"
      ref={sectionRef}
      className="reveal rounded-[32px] border border-border-grey/50 bg-white/85 p-8 shadow-lg shadow-primary-blue/10 backdrop-blur lg:p-14"
      aria-labelledby="about-scenarios-heading"
    >
      <div className="mb-10 flex flex-col gap-3 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-primary-blue/70">Before vs After</p>
        <h2 id="about-scenarios-heading" className="font-serif text-3xl font-bold text-dark-text md:text-4xl">
          From interruption fatigue to intentional collaboration.
        </h2>
      </div>
      <div className="grid gap-6">
        {SCENARIO_ROWS.map((scenario, index) => (
          <div
            key={index}
            className={classNames(
              "about-card grid gap-6 rounded-3xl border border-border-grey/60 bg-white/90 p-6 shadow-md shadow-primary-blue/10 transition-all lg:p-8",
              "sm:grid-cols-2",
            )}
            style={{ transitionDelay: `${index * 60}ms` }}
          >
            <div>
              <span className="text-xs font-semibold uppercase tracking-[0.34em] text-red-500/70">Before</span>
              {scenario.before.map((paragraph, paragraphIndex) => (
                <p
                  key={paragraph}
                  className={classNames(
                    "mt-3 text-base text-dark-text md:text-lg",
                    paragraphIndex === 0 && "font-semibold",
                  )}
                >
                  {paragraph}
                </p>
              ))}
            </div>
            <div>
              <span className="text-xs font-semibold uppercase tracking-[0.34em] text-accent-green/80">After</span>
              {scenario.after.map((paragraph, paragraphIndex) => (
                <p
                  key={paragraph}
                  className={classNames(
                    "mt-3 text-base text-dark-text md:text-lg",
                    paragraphIndex === 0 && "font-semibold",
                  )}
                >
                  {paragraph}
                </p>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function WhyTeamsNeedSection() {
  const sectionRef = useRevealOnIntersect<HTMLDivElement>();

  return (
    <section
      id="about-stats"
      ref={sectionRef}
      className="reveal snap-section rounded-[32px] border border-border-grey/50 bg-gradient-to-br from-white/95 via-white/80 to-primary-blue/10 p-8 shadow-lg shadow-primary-blue/15 backdrop-blur lg:p-14"
      aria-labelledby="about-stats-heading"
    >
      <div className="mb-10 flex flex-col gap-3 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-primary-blue/70">Why Teams Need Quell AI</p>
        <h2 id="about-stats-heading" className="font-serif text-3xl font-bold text-dark-text md:text-4xl">
          Why teams need Quell AI.
        </h2>
      </div>
      <div className="mx-auto max-w-3xl space-y-6 text-left text-base text-light-text md:text-lg">
        <p className="text-dark-text">
          Insights from today's fast-paced work environments show that modern collaboration tools often add friction instead of removing it. Quell AI is designed to simplify collaboration rather than amplify complexity, turning scattered interactions into meaningful outcomes.
        </p>
        <ul className="space-y-4">
          {NEEDS_POINTS.map((point) => (
            <li key={point.title} className="about-card rounded-3xl border border-border-grey/60 bg-white/92 p-5 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-primary-blue/70">{point.title}</p>
              <p className="mt-2 text-base text-dark-text">{point.description}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function AgentSection() {
  const sectionRef = useRevealOnIntersect<HTMLElement>();

  return (
    <section
      id="about-agent"
      ref={sectionRef}
      className="reveal grid gap-12 rounded-[32px] border border-border-grey/60 bg-white/90 p-8 shadow-lg shadow-primary-blue/15 backdrop-blur md:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:p-14"
      aria-labelledby="about-agent-heading"
    >
      <div className="flex flex-col gap-6">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-primary-blue/70">How it works</p>
        <h2 id="about-agent-heading" className="font-serif text-3xl font-bold text-dark-text md:text-4xl">
          Your time, protected. Your context, amplified.
        </h2>
        <ul className="mt-2 grid gap-4">
          {AGENT_BULLETS.map((bullet) => (
            <li key={bullet.title} className="about-card flex gap-4 rounded-2xl border border-border-grey/60 bg-white/95 p-5 shadow-sm">
              <span className="mt-1 inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary-blue/10 text-primary-blue">
                <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.75">
                  <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <div>
                <h3 className="text-base font-semibold text-dark-text">{bullet.title}</h3>
                {bullet.paragraphs.map((paragraph) => (
                  <p key={paragraph} className="mt-2 text-sm text-light-text">
                    {paragraph}
                  </p>
                ))}
              </div>
            </li>
          ))}
        </ul>
      </div>
      <div className="about-card about-connector flex flex-col justify-center gap-6 rounded-3xl border border-primary-blue/20 bg-white/85 p-8 text-center shadow-md shadow-primary-blue/15">
        <h3 className="text-sm font-semibold uppercase tracking-[0.3em] text-primary-blue/70">Context Pipeline</h3>
        <svg
          viewBox="0 0 520 160"
          role="img"
          aria-label="Sources feed into RAG agent producing outputs like minutes, tasks, answers"
          className="mx-auto h-auto w-full max-w-[460px] text-primary-blue"
        >
          <title>Quell AI context diagram</title>
          <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
            <rect x="12" y="44" width="120" height="72" rx="24" fill="rgba(42,58,91,0.08)" />
            <rect x="200" y="24" width="120" height="112" rx="26" fill="rgba(42,58,91,0.16)" />
            <rect x="388" y="12" width="120" height="136" rx="28" fill="rgba(42,58,91,0.08)" />
            <path d="M132 80h56" strokeWidth="6" />
            <path d="M320 80h56" strokeWidth="6" />
          </g>
          <text x="72" y="78" textAnchor="middle" className="fill-current text-[18px] font-semibold">
            Sources
          </text>
          <text x="260" y="70" textAnchor="middle" className="fill-current text-[16px] font-semibold">
            RAG / Agent
          </text>
          <text x="260" y="96" textAnchor="middle" className="fill-current text-[13px]">
            Policies Â· Context Â· Voice
          </text>
          <text x="448" y="60" textAnchor="middle" className="fill-current text-[16px] font-semibold">
            Outputs
          </text>
          <text x="448" y="86" textAnchor="middle" className="fill-current text-[13px]">
            Minutes Â· Tasks
          </text>
          <text x="448" y="110" textAnchor="middle" className="fill-current text-[13px]">
            Answers Â· Follow-ups
          </text>
        </svg>
      </div>
    </section>
  );
}

function WhyItMattersSection() {
  const sectionRef = useRevealOnIntersect<HTMLElement>();

  return (
    <section
      ref={sectionRef}
      className="reveal snap-section rounded-[32px] border border-border-grey/60 bg-white/92 p-8 text-center shadow-lg shadow-primary-blue/15 backdrop-blur lg:p-14"
      aria-labelledby="about-why-matters-heading"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-primary-blue/70">Why it matters</p>
      <h2 id="about-why-matters-heading" className="mt-4 font-serif text-3xl font-bold text-dark-text md:text-4xl">
        Collaboration should amplify creativity, not compete with it.
      </h2>
      <p className="mx-auto mt-6 max-w-3xl text-base text-light-text md:text-lg">
        Modern collaboration tools were built to connect people, yet they often drain focus. Quell AI reimagines collaboration as a network of understanding that adapts to your pace. Its goal is not to replace conversation; it is to restore balance between creation and communication.
      </p>
    </section>
  );
}

type VisionSectionProps = {
  activeProposalButton: "hero" | "vision" | null;
  onExploreCodex: (source: "hero" | "vision") => void;
  onJoinBeta: () => void;
};

function VisionSection({ activeProposalButton, onExploreCodex, onJoinBeta }: VisionSectionProps) {
  const sectionRef = useRevealOnIntersect<HTMLElement>();

  return (
    <section
      id="about-vision"
      ref={sectionRef}
      className="reveal rounded-[32px] border border-border-grey/60 bg-white/95 p-8 shadow-lg shadow-primary-blue/15 backdrop-blur lg:p-14"
      aria-labelledby="about-vision-heading"
    >
      <div className="flex flex-col items-center gap-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-primary-blue/70">Vision</p>
        <h2 id="about-vision-heading" className="font-serif text-3xl font-bold text-dark-text md:text-4xl">
          Beyond meetings: collaboration that understands.
        </h2>
        <p className="max-w-3xl text-base text-light-text md:text-lg">
          Quell AI keeps teams aligned today while building the memory graph that tomorrow&apos;s collaboration needs.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {ROADMAP_PHASES.map((phase) => (
            <span
              key={phase}
              className="rounded-full border border-primary-blue/30 bg-primary-blue/10 px-5 py-2 text-sm font-semibold text-primary-blue"
            >
              {phase}
            </span>
          ))}
        </div>
        <div className="flex flex-col gap-4 sm:flex-row">
          <button
            type="button"
            onClick={() => onExploreCodex('vision')}
            className={classNames(
              "proposal-button inline-flex items-center justify-center rounded-full border border-primary-blue/40 bg-primary-blue px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-blue/25 transition hover:scale-105 hover:bg-hover-blue focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50",
              activeProposalButton === "vision" && "button-active",
            )}
          >
            View Proposal
          </button>
          <button
            type="button"
            onClick={onJoinBeta}
            className="inline-flex items-center justify-center rounded-full border border-primary-blue/30 bg-white px-6 py-3 text-sm font-semibold text-primary-blue shadow-lg shadow-primary-blue/15 transition hover:scale-105 hover:bg-primary-blue/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50"
          >
            Join the Beta
          </button>
        </div>
      </div>
    </section>
  );
}
























