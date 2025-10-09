const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function initNavScroll() {
  const navbar = document.querySelector('[data-ui="navbar"]');
  if (!navbar) return;
  const setStyle = () => {
    if (window.scrollY > 24) {
      navbar.style.background = 'rgba(6, 10, 24, 0.82)';
      navbar.style.boxShadow = '0 12px 45px rgba(4, 6, 18, 0.32)';
    } else {
      navbar.style.background = 'rgba(6, 10, 24, 0.65)';
      navbar.style.boxShadow = 'none';
    }
  };
  setStyle();
  window.addEventListener('scroll', setStyle, { passive: true });
}

function smoothAnchorLinks() {
  const links = document.querySelectorAll('a[href^="#"]');
  links.forEach((link) => {
    link.addEventListener('click', (e) => {
      const target = document.querySelector(link.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: prefersReducedMotion.matches ? 'auto' : 'smooth' });
    });
  });
}

function loadPhoneModule() {
  const phoneMount = document.getElementById('phone-outer');
  if (!phoneMount) return;
  import('/assets/js/phone-3d.js').then(({ mountPhone }) => {
    mountPhone(phoneMount, { reducedMotion: prefersReducedMotion.matches });
  }).catch(() => {
    // gracefully degrade if module fails
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initNavScroll();
  smoothAnchorLinks();
  loadPhoneModule();
});
