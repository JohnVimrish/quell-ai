import{r as o,j as e}from"./main-BlRIYWXI.js";const c=`
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
`;function a(s){if(!s)return;const t=s.querySelector(".phone-time");if(!t)return;const n=new Date;t.textContent=n.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}function h(){const s=o.useRef(null);return o.useEffect(()=>{const t=s.current;if(!t)return;t.innerHTML=c;const n=t.firstElementChild;a(n);const r=window.setInterval(()=>a(n),3e4);return()=>window.clearInterval(r)},[]),e.jsx("div",{ref:s,className:"phone-mount"})}const d="/assets/story-01-Dhkj2uuZ.png",p="/assets/story-02-CBD0Je1T.png",u="/assets/story-03-CgvlBLR4.png",g="/assets/story-04-ChOcS3jn.png",m="/assets/story-05-BtXkOYu2.png",y=[{file:"story-01.png",caption:"Every VIP caller rings through immediately, while others are greeted by the copilot."},{file:"story-02.png",caption:"Summaries and action items drop into your workspace without opening another app."},{file:"story-03.png",caption:"Quell respects your schedule—no unexpected after-hours disruptions."},{file:"story-04.png",caption:"Call transcripts arrive pre-tagged so your team can focus on decisions, not logistics."},{file:"story-05.png",caption:"Share wrap-ups instantly with stakeholders in a polished, branded format."}];function f(s){return`/reference_images/${s}`}function x(){return e.jsx("section",{className:"section-padding storytelling-gallery",children:y.map(({file:s,caption:t})=>{const n=new URL(Object.assign({"../assets/images/story-01.png":d,"../assets/images/story-02.png":p,"../assets/images/story-03.png":u,"../assets/images/story-04.png":g,"../assets/images/story-05.png":m})[`../assets/images/${s}`],import.meta.url).href,r=f(s);return e.jsxs("article",{className:"story-item",children:[e.jsx("img",{src:r,onError:l=>{const i=l.currentTarget;i.src!==n&&(i.src=n)},alt:t,loading:"lazy",decoding:"async"}),e.jsx("div",{className:"story-caption",children:e.jsx("p",{children:t})})]},s)})})}function v(){return e.jsxs("div",{className:"landing-page",children:[e.jsxs("section",{className:"hero section-padding",children:[e.jsxs("div",{children:[e.jsx("h1",{className:"headline",children:"Your communicator copilot that respects every call"}),e.jsx("p",{className:"subheadline",children:"Quell-AI filters the noise, captures the signal, and keeps your attention on high-impact work."}),e.jsxs("div",{className:"hero-actions",children:[e.jsx("button",{className:"button-primary",children:"Start free trial"}),e.jsx("button",{className:"button-outline",children:"Book a demo"})]})]}),e.jsx(h,{})]}),e.jsxs("section",{className:"section-padding glass-panel",children:[e.jsx("h2",{children:"Why choose Quell-AI"}),e.jsxs("ul",{className:"features-grid",children:[e.jsxs("li",{className:"feature-card",children:[e.jsx("h3",{children:"Call Screening"}),e.jsx("p",{children:"Answer the right conversations—Quell politely handles the rest."})]}),e.jsxs("li",{className:"feature-card",children:[e.jsx("h3",{children:"Memory on Tap"}),e.jsx("p",{children:"Every call summarized instantly with action items you can trust."})]}),e.jsxs("li",{className:"feature-card",children:[e.jsx("h3",{children:"Trusted Boundaries"}),e.jsx("p",{children:"Respect priority contacts and protect your evenings without missing a beat."})]})]})]}),e.jsx(x,{})]})}export{v as default};
