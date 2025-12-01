import{j as t}from"./main-DdieF_OH.js";function c(){return t.jsxs("div",{className:"animated-bg","aria-hidden":"true",children:[t.jsx("div",{className:"shape1"}),t.jsx("div",{className:"shape2"}),t.jsx("div",{className:"shape3"})]})}const r="https://cdn.tailwindcss.com?plugins=forms,container-queries",o=`tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'primary-blue': 'var(--color-primary-blue)',
        'secondary-grey': 'var(--color-secondary-grey)',
        'accent-metallic': 'var(--color-accent-metallic)',
        'light-background': 'var(--color-light-background)',
        'dark-text': 'var(--color-dark-text)',
        'light-text': 'var(--color-light-text)',
        'border-grey': 'var(--color-border-grey)',
        'hover-blue': 'var(--color-hover-blue)',
        'accent-green': 'var(--color-accent-green)',
      },
      fontFamily: {
        serif: ['Merriweather', 'serif'],
        sans: ['Open Sans', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.375rem',
        md: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
        '2xl': '1.5rem',
        full: '9999px',
      },
    },
  },
};`,n=`
.nav-3d,.btn-3d{will-change:transform,box-shadow;transform:translateZ(0);transition:transform .2s ease,box-shadow .2s ease,background-color .2s ease,color .2s ease;}
.nav-3d{box-shadow:0 6px 18px rgba(42,58,91,.08);}
.nav-3d:hover{transform:translateY(-2px);box-shadow:0 12px 26px rgba(42,58,91,.16);}
.nav-3d:active{transform:translateY(0);box-shadow:0 8px 20px rgba(42,58,91,.14);}
.btn-3d{box-shadow:0 10px 24px rgba(42,58,91,.22);}
.btn-3d:hover{transform:translateY(-2px);box-shadow:0 16px 32px rgba(42,58,91,.28);}
.btn-3d:active{transform:translateY(0);box-shadow:0 8px 18px rgba(42,58,91,.2);}
.active-nav{background:var(--color-primary-blue);color:#fff!important;box-shadow:0 18px 36px rgba(42,58,91,.28);}
`,i=`
.book-container{perspective:2500px;}
.book{position:relative;width:100%;height:600px;transform-style:preserve-3d;transition:transform .5s;}
.page{position:absolute;width:50%;height:100%;top:0;left:50%;transform-origin:left center;transition:transform 1.5s cubic-bezier(.645,.045,.355,1);backface-visibility:hidden;transform-style:preserve-3d;}
.page.flipped{transform:rotateY(-180deg);}
.page-content{position:absolute;width:100%;height:100%;backface-visibility:hidden;transform-style:preserve-3d;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.75);backdrop-filter:blur(16px);}
.page-content::before{content:'';position:absolute;inset:0;background:linear-gradient(to right,rgba(255,255,255,.1)0%,rgba(255,255,255,0)10%);transition:opacity .5s ease;opacity:0;z-index:10;}
.page-content::after{content:'';position:absolute;inset:0;background:linear-gradient(to left,rgba(0,0,0,.1)0%,rgba(0,0,0,0)10%);box-shadow:inset -5px 0 15px -5px rgba(0,0,0,.2);transition:opacity .5s ease;opacity:0;z-index:10;}
.page.turning .page-front::before{opacity:1;transition-delay:.2s;}
.page.turning .page-back::after{opacity:1;transition-delay:.2s;}
.page.flipped .page-front::before,.page.flipped .page-back::after{opacity:0;transition-delay:0s;}
.page-front,.page-back{overflow-y:auto;}
.page-back{transform:rotateY(180deg);}
.book-cover{position:absolute;width:50%;height:100%;top:0;left:0;transform-origin:right center;background:rgba(42,58,91,.9);border-radius:10px 0 0 10px;box-shadow:0 10px 30px rgba(0,0,0,.2);z-index:10;border:1px solid rgba(255,255,255,.1);}
.book-back-cover{position:absolute;width:50%;height:100%;top:0;right:0;background:rgba(42,58,91,.9);border-radius:0 10px 10px 0;box-shadow:0 10px 30px rgba(0,0,0,.2);z-index:-1;}
.page-turn-btn{position:absolute;bottom:20px;z-index:50;background:rgba(255,255,255,.9);border:1px solid var(--color-border-grey);border-radius:9999px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .3s ease;box-shadow:0 4px 15px rgba(0,0,0,.1);}
.page-turn-btn:hover{background:var(--color-primary-blue);color:#fff;transform:scale(1.1);}
.page-turn-btn.prev{left:20px;}
.page-turn-btn.next{right:20px;}
`,s="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined";function d({includeBookStyles:a=!1}={}){if(!(typeof document>"u")){if(!document.querySelector('script[data-qlx="public-tailwind-cdn"]')){const e=document.createElement("script");e.src=r,e.async=!0,e.dataset.qlx="public-tailwind-cdn",document.head.appendChild(e)}if(!document.querySelector('script[data-qlx="public-tailwind-config"]')){const e=document.createElement("script");e.type="text/javascript",e.dataset.qlx="public-tailwind-config",e.innerHTML=o,document.head.appendChild(e)}if(!document.querySelector('style[data-qlx="public-tailwind-base"]')){const e=document.createElement("style");e.type="text/tailwindcss",e.dataset.qlx="public-tailwind-base",e.innerHTML=n,document.head.appendChild(e)}if(a&&!document.querySelector('style[data-qlx="public-tailwind-book"]')){const e=document.createElement("style");e.type="text/tailwindcss",e.dataset.qlx="public-tailwind-book",e.innerHTML=i,document.head.appendChild(e)}if(!document.querySelector('link[data-qlx="material-symbols"]')){const e=document.createElement("link");e.rel="stylesheet",e.href=s,e.dataset.qlx="material-symbols",document.head.appendChild(e)}}}export{c as F,d as e};
