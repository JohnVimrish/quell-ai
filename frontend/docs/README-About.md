# Quell AI About Section Guide

This document explains how to maintain the new story-driven sections that live on `LandingPage.tsx` (rendered directly below the hero and above the flipbook).

## Content Sources

All copy and numbers are co-located with the page component (`frontend/src/pages/LandingPage.tsx`):

| Content block | Constant |
| --- | --- |
| Before / After rows | `SCENARIO_ROWS` |
| Stats chips | `STATS` (`value`, optional `suffix`, `label`) |
| Agent bullets | `AGENT_BULLETS` |
| Roadmap chips | `ROADMAP_PHASES` |

Update these arrays to refresh text or inject CMS driven values. Components read directly from the constants so no additional wiring is needed.

## Animation Controls

Reveal and motion effects are shared:

* `useRevealOnIntersect` (in `frontend/src/hooks/useRevealOnIntersect.ts`) handles scroll-triggered fades. To disable for a section, remove the hook call or pass `{ once: false }` for repeated triggers.
* `usePrefersReducedMotion` honors `prefers-reduced-motion`. Users who request reduced motion automatically see static content (no fades, no count-up).
* Stat count-up animation calls `useCountUp`. Pass `disabled: true` if you need to turn the animation off manually.

## Image & Illustration Specs

* Hero/Blueprint illustration reference: 600 × 600 PNG (served via HTTPS, `loading="lazy"`, `decoding="async"`).
* Diagram in Agent section is inline SVG for crisp scaling; keep width ≤ 520px to avoid overflow.

If you swap assets, prefer SVG where possible or 2× PNG with transparent background. Always provide meaningful `alt` text.

## CTA Behaviour

* “Explore the Codex” buttons call `handleScrollToCodex`, scrolling to the flipbook section (`<section id="codex">`).
* “Join the Beta” navigates to `/signup`. Change the handler to point at a modal or mailto as needed.

## Accessibility Checklist

* Each section exposes `aria-labelledby` tied to an `<h2>`.
* Interactive cards implement `tabIndex={0}` and `:focus-visible` outlines (see `LandingPage.css`).
* Animations are skipped when `prefers-reduced-motion: reduce`.

## Styling

Shared styles live in `frontend/src/pages/LandingPage.css`. Key utility classes:

* `.reveal` / `.is-visible` – fade-in animation.
* `.about-card`, `.about-stat-chip` – hover / focus lift.
* `.about-float` – soft background drift (disabled under reduced motion).

Adjust design tokens via existing CSS variables (`--color-*`, `--shadow-*`, etc.) to remain on-brand.

