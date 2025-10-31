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
            <h3>Quell-Ai actively shields your time.</h3>
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

function updateTime(root) {
  const timeEl = root.querySelector('.phone-time');
  if (!timeEl) return;
  const now = new Date();
  timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function initParallax(root, reducedMotion) {
  if (reducedMotion) return;
  const handler = (e) => {
    const rect = root.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    const rotY = (x - 0.5) * 16;
    const rotX = -(y - 0.5) * 16;
    root.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg)`;
  };
  const reset = () => {
    root.style.transform = 'rotateX(8deg) rotateY(-8deg)';
  };
  root.addEventListener('mousemove', handler);
  root.addEventListener('mouseleave', reset);
  reset();
}

export function mountPhone(target, { reducedMotion = false } = {}) {
  target.innerHTML = PHONE_TEMPLATE;
  const phone = target.firstElementChild;
  updateTime(phone);
  setInterval(() => updateTime(phone), 30000);
  initParallax(phone, reducedMotion);
}
