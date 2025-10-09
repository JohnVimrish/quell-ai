import{r as o,j as e}from"./main-U5VUWQoG.js";const a=`
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
`;function r(t){if(!t)return;const s=t.querySelector(".phone-time");if(!s)return;const n=new Date;s.textContent=n.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}function l(){const t=o.useRef(null);return o.useEffect(()=>{const s=t.current;if(!s)return;s.innerHTML=a;const n=s.firstElementChild;r(n);const i=window.setInterval(()=>r(n),3e4);return()=>window.clearInterval(i)},[]),e.jsx("div",{ref:t,className:"phone-mount"})}const c="/assets/story-01-Dhkj2uuZ.png",d="/assets/story-02-CBD0Je1T.png",h="/assets/story-03-CgvlBLR4.png",p="/assets/story-04-ChOcS3jn.png",m="/assets/story-05-BtXkOYu2.png",u={"story-01.png":c,"story-02.png":d,"story-03.png":h,"story-04.png":p,"story-05.png":m},g=[{file:"story-01.png",caption:"Every VIP caller rings through immediately, while others are greeted by the copilot."},{file:"story-02.png",caption:"Summaries and action items drop into your workspace without opening another app."},{file:"story-03.png",caption:"Quell respects your schedule—no unexpected after-hours disruptions."},{file:"story-04.png",caption:"Call transcripts arrive pre-tagged so your team can focus on decisions, not logistics."},{file:"story-05.png",caption:"Share wrap-ups instantly with stakeholders in a polished, branded format."}];function y(){return e.jsx("section",{className:"section-padding storytelling-gallery",children:g.map(({file:t,caption:s})=>{const n=u[t];return e.jsxs("article",{className:"story-item",children:[e.jsx("img",{src:n,alt:s,loading:"lazy",decoding:"async"}),e.jsx("div",{className:"story-caption",children:e.jsx("p",{children:s})})]},t)})})}function v(){return e.jsxs("div",{className:"landing-page",children:[e.jsxs("section",{className:"hero section-padding",children:[e.jsxs("div",{children:[e.jsx("h1",{className:"headline",children:"Your communicator copilot that respects every call"}),e.jsx("p",{className:"subheadline",children:"Quell-AI filters the noise, captures the signal, and keeps your attention on high-impact work."}),e.jsxs("div",{className:"hero-actions",children:[e.jsx("button",{className:"button-primary",children:"Start free trial"}),e.jsx("button",{className:"button-outline",children:"Book a demo"})]})]}),e.jsx(l,{})]}),e.jsxs("section",{className:"section-padding glass-panel",children:[e.jsx("h2",{children:"Why choose Quell-AI"}),e.jsxs("ul",{className:"features-grid",children:[e.jsxs("li",{className:"feature-card",children:[e.jsx("h3",{children:"Call Screening"}),e.jsx("p",{children:"Answer the right conversations—Quell politely handles the rest."})]}),e.jsxs("li",{className:"feature-card",children:[e.jsx("h3",{children:"Memory on Tap"}),e.jsx("p",{children:"Every call summarized instantly with action items you can trust."})]}),e.jsxs("li",{className:"feature-card",children:[e.jsx("h3",{children:"Trusted Boundaries"}),e.jsx("p",{children:"Respect priority contacts and protect your evenings without missing a beat."})]})]})]}),e.jsx(y,{})]})}export{v as default};
