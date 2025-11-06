(function () {
  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function clamp(v, a, b) {
    return Math.max(a, Math.min(b, v));
  }

  function setupFlipbook() {
    const book = document.getElementById("book");
    if (!book) return;

    const pages = Array.from(book.querySelectorAll(".page"));
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const audio = document.getElementById("page-flip-sound");
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let currentLocation = 1;
    const maxLocation = pages.length + 1;

    function playSound() {
      if (!audio) return;
      try {
        audio.currentTime = 0;
        audio.volume = 0.2;
        audio.play().catch(() => {});
        const fade = setInterval(() => {
          if (audio.volume > 0.04) {
            audio.volume -= 0.04;
          } else {
            audio.pause();
            clearInterval(fade);
          }
        }, 120);
      } catch (_) {}
    }

    function openBook() {
      book.style.transform = "translateX(50%)";
      if (prevBtn) prevBtn.style.transform = "translateX(-180px)";
      if (nextBtn) nextBtn.style.transform = "translateX(180px)";
    }

    function closeBook(atStart) {
      book.style.transform = atStart ? "translateX(0%)" : "translateX(100%)";
      if (prevBtn) prevBtn.style.transform = "translateX(0px)";
      if (nextBtn) nextBtn.style.transform = "translateX(0px)";
    }

    function animateFlip(pageIndex, direction, done) {
      const page = pages[pageIndex];
      if (!page) {
        done && done();
        return;
      }

      playSound();

      const forward = direction === "next";
      const duration = prefersReduced ? 250 : 900;
      const start = performance.now();

      const initialAngle = forward ? 0 : -180;
      const targetAngle = forward ? -180 : 0;
      const originalOrigin = page.style.transformOrigin || "left center";
      page.style.transformOrigin = forward ? "left center" : "right center";

      const originalZ = page.style.zIndex;
      page.style.zIndex = String(100 + pageIndex);
      page.classList.add("is-flipping");

      function frame(now) {
        const t = clamp((now - start) / duration, 0, 1);
        const k = easeInOutCubic(t);
        const angle = initialAngle + (targetAngle - initialAngle) * k;
        const bend = 12 * Math.sin(Math.PI * k);
        const shade = 0.85 * Math.sin(Math.PI * k);
        const gloss = 0.55 * Math.sin(Math.PI * k);

        page.style.setProperty("--angle", angle + "deg");
        page.style.setProperty("--bend", bend.toFixed(3));
        page.style.setProperty("--shade", shade.toFixed(3));
        page.style.setProperty("--gloss", gloss.toFixed(3));

        if (t < 1) {
          requestAnimationFrame(frame);
        } else {
          page.classList.remove("is-flipping");
          page.style.removeProperty("--angle");
          page.style.removeProperty("--bend");
          page.style.removeProperty("--shade");
          page.style.removeProperty("--gloss");
          page.style.transformOrigin = originalOrigin;
          if (forward) {
            page.classList.add("flipped");
            page.style.zIndex = String(pageIndex + 1);
          } else {
            page.classList.remove("flipped");
            page.style.zIndex = originalZ || String(pages.length - pageIndex);
          }
          done && done();
        }
      }

      requestAnimationFrame(frame);
    }

    function goNextPage() {
      if (currentLocation >= maxLocation) return;
      const index = currentLocation - 1;
      if (currentLocation === 1) {
        openBook();
      }
      if (currentLocation === pages.length) {
        animateFlip(index, "next", () => {
          closeBook(false);
        });
      } else {
        animateFlip(index, "next");
      }
      currentLocation++;
    }

    function goPrevPage() {
      if (currentLocation <= 1) return;
      const index = currentLocation - 2;
      if (currentLocation === 2) {
        animateFlip(index, "prev", () => {
          closeBook(true);
        });
      } else if (currentLocation === pages.length + 1) {
        openBook();
        animateFlip(index, "prev");
      } else {
        animateFlip(index, "prev");
      }
      currentLocation--;
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", goPrevPage);
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", goNextPage);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupFlipbook);
  } else {
    setupFlipbook();
  }
})();
