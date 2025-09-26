import { useEffect, useRef } from "react";

const PHONE_TEMPLATE = `
  <div class="phone-outer" role="presentation">
    <div class="phone-frame">
      <div class="phone-glare"></div>
      <div class="phone-screen">
        <div class="phone-notch">
          <div class="phone-speaker"></div>
          <div class="phone-camera"></div>
        </div>
        <div class="phone-content">
          <header class="phone-status">
            <span class="phone-time"></span>
            <span class="phone-signal">AI MODE</span>
          </header>
          <main class="phone-body">
            <h3>Quell-AI actively shields your time.</h3>
            <ul>
              <li>Screens unknown callers politely.</li>
              <li>Summarizes conversations instantly.</li>
              <li>Respects important contact boundaries.</li>
            </ul>
          </main>
          <footer class="phone-action">
            <button class="phone-button">Enable Copilot</button>
          </footer>
        </div>
      </div>
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

function initParallax(root: HTMLElement | null, reducedMotion: boolean) {
  if (!root || reducedMotion) return;
  const handler = (event: MouseEvent) => {
    const rect = root.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    const rotY = (x - 0.5) * 16;
    const rotX = -(y - 0.5) * 16;
    root.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg)`;
  };
  const reset = () => {
    root.style.transform = "rotateX(8deg) rotateY(-8deg)";
  };
  root.addEventListener("mousemove", handler);
  root.addEventListener("mouseleave", reset);
  reset();
  return () => {
    root.removeEventListener("mousemove", handler);
    root.removeEventListener("mouseleave", reset);
  };
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
    const cleanParallax = initParallax(phone, window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    return () => {
      window.clearInterval(interval);
      if (cleanParallax) cleanParallax();
    };
  }, []);

  return <div ref={containerRef} className="phone-mount" />;
}
