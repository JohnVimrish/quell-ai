import { useEffect, useRef } from "react";

const PHONE_TEMPLATE = `
  <div class="hero-phone-frame" role="presentation">
    <div class="hero-phone-display">
      <header class="hero-phone-status">
        <span class="phone-time"></span>
      </header>
      <main class="hero-phone-content">
        <section class="hero-phone-video">
          <div class="video-container">
            <video 
              class="phone-video" 
              controls 
              poster="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3Crect fill='%23f5f5f5' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23737373' font-family='Arial' font-size='20'%3EQuell-AI Demo%3C/text%3E%3C/svg%3E"
            >
              <source src="https://www.w3schools.com/html/mov_bbb.mp4" type="video/mp4">
              Your browser does not support the video tag.
            </video>
            <div class="video-overlay">
              <svg class="play-icon" viewBox="0 0 24 24" fill="white" width="48" height="48">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </div>
          </div>
          <p style="margin: 12px 0 0; color: var(--color-grey-700); font-size: 0.9rem; text-align: center;">
            Watch how Quell-AI handles your calls
          </p>
        </section>
        <section class="hero-phone-card" style="margin-top: 12px;">
          <h4 style="margin: 0 0 8px; font-size: 1rem; font-weight: 700; color: var(--color-grey-900);">Quick Stats</h4>
          <p style="margin: 0; color: var(--color-grey-700); font-size: 0.85rem; line-height: 1.6;">
            ✓ 2 VIP calls connected<br>
            ✓ 5 calls screened<br>
            ✓ 3 AI summaries ready
          </p>
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
