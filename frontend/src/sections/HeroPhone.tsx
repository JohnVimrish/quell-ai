import { useEffect, useRef } from "react";

const PHONE_TEMPLATE = `
  <div class="hero-phone-frame" role="presentation">
    <div class="hero-phone-display">
      <header class="hero-phone-status">
        <span class="phone-time"></span>
      </header>
      <main class="hero-phone-content">
        <section class="hero-phone-card">
          <h4 style="margin: 0 0 12px; font-size: 1.1rem; font-weight: 700; color: var(--color-grey-900);">Inbox Summary</h4>
          <ul style="margin: 0; padding: 0 0 0 20px; color: var(--color-grey-700); font-size: 0.95rem; line-height: 1.8;">
            <li>2 VIP calls connected</li>
            <li>5 non-urgent calls deferred</li>
            <li>AI generated 3 quick summaries</li>
          </ul>
        </section>
        <section class="hero-phone-card">
          <h4 style="margin: 0 0 12px; font-size: 1.1rem; font-weight: 700; color: var(--color-grey-900);">Next Actions</h4>
          <p style="margin: 0 0 16px; color: var(--color-grey-700); font-size: 0.95rem; line-height: 1.6;">Review meeting notes delivered to your workspace with one tap.</p>
          <button class="button-primary" style="padding: 10px 20px; font-size: 0.9rem; width: 100%;">Open Copilot</button>
        </section>
      </main>
    </div>
  </div>
`;

function updateTime(root: HTMLElement | null) {
  if (!root) return;
  const timeEl = root.querySelector<HTMLElement>(".phone-time");
  if (!timeEl) return;
  const now = new Date();
  timeEl.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function HeroPhone() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = containerRef.current;
    if (!mount) return;
    mount.innerHTML = PHONE_TEMPLATE;
    const phone = mount.firstElementChild as HTMLElement | null;
    updateTime(phone);
    const interval = window.setInterval(() => updateTime(phone), 30000);
    return () => window.clearInterval(interval);
  }, []);

  return <div ref={containerRef} className="phone-mount" />;
}
