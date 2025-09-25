import React, { useEffect, useRef, useState } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Phone, Mic, PhoneOff, Volume2, Sparkles, ChevronRight, ChevronLeft } from "lucide-react";

// Motion‑activated 3D UI demo (light palette) with:
// - Route-aware nav highlighting
// - Reusable FeatureCard component
// - Section microinteractions and in-view animations

export default function CallAssistantShowcase(){
  const [route, setRoute] = useState("home");
  useEffect(()=>{
    const hash = window.location.hash.replace('#','');
    if(hash) setRoute(hash);
    const onHash = ()=> setRoute(window.location.hash.replace('#','') || 'home');
    window.addEventListener('hashchange', onHash);
    return ()=> window.removeEventListener('hashchange', onHash);
  },[])

  return (
    <div className="min-h-screen w-full bg-[#f9fbff] text-slate-900 overflow-hidden relative">
      <AuroraField/>
      <header className="relative z-10 max-w-7xl mx-auto px-6 pt-8">
        <div className="flex items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 via-emerald-400 to-lime-300 shadow-[0_10px_30px_rgba(56,189,248,0.35)]">
              <Sparkles className="h-5 w-5 text-white"/>
            </span>
            <strong className="text-lg tracking-tight">Voxa — Phone Assistant</strong>
          </div>
          <Nav route={route} onNavigate={(r)=>{ setRoute(r); window.location.hash = r; }}/>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 pb-28">
        <HeroBlock/>
        {/* Aero-style workspace like your reference */}
        <Section id="workspace" title="Workspace (Aero 3D)">
          <AeroBoard/>
        </Section>
        <Section id="screens" title="Screens">
          <ScreensCarousel/>
        </Section>
        <Section id="features" title="Highlights">
          <div className="grid lg:grid-cols-3 gap-4">
            <FeatureCard title="Live transcript" caption="Real‑time voice to text with action extraction." tone="from-cyan-50 to-white"/>
            <FeatureCard title="Spam shield" caption="Blocks robocalls; lets VIP calls through." tone="from-emerald-50 to-white"/>
            <FeatureCard title="Auto‑summary" caption="Key points and tasks sent after every call." tone="from-lime-50 to-white"/>
          </div>
        </Section>
        <FooterBlock/>
      </main>
    </div>
  )
}

function Nav({ route, onNavigate }){
  const items = [
    { k:"home", label:"Home" },
    { k:"screens", label:"Screens" },
    { k:"features", label:"Features" },
  ];
  return (
    <nav className="relative">
      <ul className="flex items-center gap-2 bg-white/70 backdrop-blur rounded-2xl border border-slate-200 p-1">
        {items.map((it)=>{
          const active = route===it.k || (route==='home' && it.k==='home');
          return (
            <li key={it.k}>
              <button onClick={()=>onNavigate(it.k)}
                className={`relative px-4 py-2 rounded-xl text-sm transition ${active?"text-white":"text-slate-700 hover:text-slate-900"}`}
              >
                {active && (
                  <motion.span
                    layoutId="nav-pill"
                    className="absolute inset-0 rounded-xl bg-slate-900"
                    transition={{ type:"spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{it.label}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

function Section({ id, title, children }){
  return (
    <section id={id} className="mt-16">
      <motion.h2
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity:1, y:0 }}
        viewport={{ once: true, amount: .6 }}
        transition={{ duration:.5 }}
        className="text-2xl font-semibold mb-4"
      >{title}</motion.h2>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity:1, y:0 }}
        viewport={{ once: true, amount: .6 }}
        transition={{ duration:.55 }}
      >
        {children}
      </motion.div>
    </section>
  )
}

function FeatureCard({ title, caption, tone }){
  return (
    <motion.div
      whileHover={{ y:-4 }}
      transition={{ type:"spring", stiffness: 300, damping: 20 }}
      className={`rounded-2xl p-4 border shadow-inner bg-gradient-to-b ${tone} border-slate-100`}
    >
      <div className="text-[13px] text-slate-500 mb-1">{title}</div>
      <div className="text-slate-700">{caption}</div>
    </motion.div>
  )
}

function AuroraField(){
  const ref = useRef(null)
  const mx = useMotionValue(0)
  const my = useMotionValue(0)
  const glowX = useSpring(useTransform(mx, [0, 1], ["0%", "100%"]), { stiffness: 120, damping: 30 })
  const glowY = useSpring(useTransform(my, [0, 1], ["0%", "100%"]), { stiffness: 120, damping: 30 })

  useEffect(()=>{
    const el = ref.current
    if(!el) return
    const onMove = (e)=>{
      const r = el.getBoundingClientRect()
      mx.set((e.clientX - r.left) / r.width)
      my.set((e.clientY - r.top) / r.height)
    }
    window.addEventListener("mousemove", onMove)
    return ()=> window.removeEventListener("mousemove", onMove)
  },[])

  return (
    <div ref={ref} className="absolute inset-0 -z-0">
      {/* big soft gradient base with cooler tones */}
      <div className="absolute -inset-20 bg-[radial-gradient(55%_60%_at_20%_20%,#e0f7ff_0%,transparent_60%),radial-gradient(55%_60%_at_85%_15%,#e8ffe3_0%,transparent_60%),radial-gradient(70%_70%_at_60%_80%,#fff8e1_0%,transparent_65%)]"/>
      {/* animated blobs */}
      <motion.div
        aria-hidden
        className="absolute -inset-10 mix-blend-multiply blur-3xl opacity-60"
        animate={{ x: [0, 20, -10, 0], y: [0, -10, 15, 0] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
        style={{
          background:
            "radial-gradient(30%_30%_at_30%_30%, #b3e5fc 0, transparent 70%),"+
            "radial-gradient(28%_28%_at_72%_35%, #c8e6c9 0, transparent 70%),"+
            "radial-gradient(40%_40%_at_60%_75%, #fff59d 0, transparent 70%)",
        }}
      />
      {/* cursor-reactive glow */}
      <motion.div
        className="absolute size-64 rounded-full pointer-events-none"
        style={{ left: glowX, top: glowY, translateX: "-50%", translateY: "-50%",
          background:
            "radial-gradient(closest-side, rgba(56,189,248,.35), rgba(56,189,248,0) 70%)" }}
      />
    </div>
  )
}

function HeroBlock(){
  return (
    <section className="pt-12 grid md:grid-cols-2 gap-10 items-center">
      <div>
        <span className="inline-block px-3 py-1 rounded-full border border-cyan-300/70 bg-white/60 backdrop-blur text-cyan-700 text-xs shadow-sm">
          Not another dark UI ✨
        </span>
        <h1 className="mt-4 text-5xl md:text-6xl font-semibold tracking-tight leading-[1.05]">
          Motion‑Activated <span className="bg-gradient-to-r from-cyan-500 via-emerald-500 to-lime-500 bg-clip-text text-transparent">3D UI</span> for your call assistant
        </h1>
        <p className="mt-4 text-[17px] text-slate-700 max-w-prose">
          Cursor‑driven parallax, draggable screens, tactile controls, and a playful bright backdrop. Swap palettes or plug in your own screens—the framework handles the motion.
        </p>
        <div className="mt-6 flex items-center gap-3">
          <a href="#screens" className="px-5 py-3 rounded-2xl bg-slate-900 text-white shadow-[0_14px_30px_rgba(2,6,23,0.2)] hover:shadow-[0_16px_36px_rgba(2,6,23,0.28)] active:translate-y-[1px] inline-flex items-center gap-2">
            Try the carousel <ChevronRight className="h-5 w-5"/>
          </a>
          <a href="#features" className="px-5 py-3 rounded-2xl bg-white/70 backdrop-blur border border-slate-200 text-slate-900 hover:bg-white">Explore features</a>
        </div>
      </div>

      <ParallaxPhone/>
    </section>
  )
}

// 3D tilted phone reacting to cursor
function ParallaxPhone(){
  const cardRef = useRef(null)
  const rx = useSpring(0, { stiffness: 120, damping: 12 })
  const ry = useSpring(0, { stiffness: 120, damping: 12 })

  const onMove = (e)=>{
    const el = cardRef.current
    if(!el) return
    const r = el.getBoundingClientRect()
    const px = (e.clientX - r.left) / r.width - 0.5
    const py = (e.clientY - r.top) / r.height - 0.5
    ry.set(px * 16) // rotateY
    rx.set(-py * 12) // rotateX
  }
  const onLeave = ()=>{ rx.set(0); ry.set(0) }

  return (
    <div className="relative h-full flex items-center justify-center">
      <motion.div
        ref={cardRef}
        onMouseMove={onMove}
        onMouseLeave={onLeave}
        className="[perspective:1200px]"
      >
        <motion.div
          style={{ rotateX: rx, rotateY: ry, transformStyle: "preserve-3d" }}
          className="relative w-[320px] h-[640px] mx-auto rounded-[36px] shadow-[0_30px_60px_rgba(2,6,23,0.35)]"
        >
          {/* phone frame */}
          <div className="absolute inset-0 rounded-[36px] bg-gradient-to-b from-slate-900 to-slate-800" style={{ transform: "translateZ(0px)" }}/>
          {/* screen */}
          <div className="absolute inset-[10px] rounded-[28px] overflow-hidden bg-gradient-to-b from-white to-emerald-50" style={{ transform: "translateZ(35px)" }}>
            <div className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-400 to-lime-400 shadow-[0_12px_24px_rgba(56,189,248,0.35)]"/>
              <div>
                <div className="text-slate-800 font-medium">Alex (AI)</div>
                <div className="text-xs text-slate-500">00:24 • Active call</div>
              </div>
            </div>
            <VoiceWave/>
            <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-3">
              <Knob icon={<Volume2 className="h-5 w-5"/>} gloss="from-emerald-300 to-emerald-500"/>
              <Knob icon={<PhoneOff className="h-5 w-5"/>} gloss="from-lime-300 to-lime-500"/>
              <Knob icon={<Mic className="h-5 w-5"/>} gloss="from-cyan-300 to-cyan-500"/>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

function Knob({ icon, gloss }){
  return (
    <button className={`size-14 rounded-2xl grid place-items-center text-slate-900 bg-white border border-slate-200 shadow-[8px_10px_24px_rgba(2,6,23,0.15),inset_-6px_-10px_20px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] active:translate-y-[1px] relative overflow-hidden`}
      style={{ transform: "translateZ(50px)" }}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gloss} opacity-40`}/>
      <div className="relative z-10">{icon}</div>
    </button>
  )
}

function VoiceWave(){
  const bars = new Array(28).fill(0)
  return (
    <div className="mt-10 mb-20 px-8">
      <div className="h-36 flex items-end gap-1.5 justify-center" aria-hidden>
        {bars.map((_,i)=> (
          <motion.span key={i}
            className="w-2 rounded-full bg-gradient-to-b from-cyan-400 to-lime-400 shadow-[0_10px_16px_rgba(56,189,248,0.35)]"
            animate={{ height: [16, 140 - (i%5)*8, 28] }}
            transition={{ duration: 1 + (i%5)*0.08, repeat: Infinity, ease: "easeInOut" }}
            style={{ display: "inline-block" }}
          />
        ))}
      </div>
    </div>
  )
}

function ScreensCarousel(){
  const screens = [
    { name:"Call Screen", node:<CallScreen/> },
    { name:"Inbox & Summaries", node:<InboxScreen/> },
    { name:"Analytics", node:<AnalyticsScreen/> },
  ]
  const [idx,setIdx] = useState(0)
  const next = ()=> setIdx((p)=> (p+1)%screens.length)
  const prev = ()=> setIdx((p)=> (p-1+screens.length)%screens.length)

  useEffect(()=>{ const t = setInterval(next, 5200); return ()=> clearInterval(t) },[])

  return (
    <section id="screens" className="mt-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-slate-700">Interactive carousel</h3>
        <div className="flex gap-2">
          <button onClick={prev} className="size-9 rounded-xl bg-white/70 border border-slate-200 grid place-items-center hover:bg-white active:translate-y-[1px]"><ChevronLeft className="h-5 w-5"/></button>
          <button onClick={next} className="size-9 rounded-xl bg-slate-900 text-white grid place-items-center hover:opacity-90 active:translate-y-[1px]"><ChevronRight className="h-5 w-5"/></button>
        </div>
      </div>

      <motion.div className="relative">
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 20, scale:.98 }}
          animate={{ opacity: 1, y: 0, scale:1 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ type: "spring", stiffness: 140, damping: 18 }}
        >
          <motion.div drag="x" dragConstraints={{ left: -80, right: 80 }} whileTap={{ cursor: "grabbing" }}
            className="rounded-3xl bg-white/70 backdrop-blur border border-slate-200 p-6 shadow-[0_24px_60px_rgba(2,6,23,0.12)]" >
            <div className="flex items-center gap-3 mb-4">
              {screens.map((s,i)=> (
                <button key={s.name} onClick={()=>setIdx(i)}
                  className={`px-3 py-1 rounded-full text-xs border ${i===idx?"bg-slate-900 text-white border-slate-900":"bg-white/70 border-slate-200"}`}>{s.name}</button>
              ))}
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="rounded-2xl p-4 bg-gradient-to-b from-emerald-50 to-white border border-emerald-100">
                {screens[idx].node}
              </div>
              <div className="rounded-2xl p-4 bg-gradient-to-b from-cyan-50 to-white border border-cyan-100">
                <ParallaxStats/>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </motion.div>
    </section>
  )
}

function CallScreen(){
  return (
    <div className="aspect-[4/3] rounded-xl p-4 bg-white border border-slate-100 shadow-inner">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-cyan-400 to-lime-400"/>
        <div className="text-sm text-slate-600">Alex • Live transcript</div>
      </div>
      <div className="mt-4 space-y-2 text-sm">
        <div className="px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-100 w-fit">Hi! Are we still on for 3 PM?</div>
        <div className="px-3 py-2 rounded-lg bg-cyan-50 border border-cyan-100 w-fit ml-auto">Yes—invites sent. Agenda attached.</div>
        <div className="px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-100 w-fit">Great, talk soon!</div>
      </div>
      <div className="mt-4 flex justify-center gap-3">
        <button className="px-4 py-2 rounded-xl bg-lime-500 text-white shadow hover:opacity-90"><Phone className="inline mr-2 h-4 w-4"/>Call back</button>
        <button className="px-4 py-2 rounded-xl bg-slate-900 text-white shadow hover:opacity-90"><Mic className="inline mr-2 h-4 w-4"/>Auto‑reply</button>
      </div>
    </div>
  )
}

function InboxScreen(){
  return (
    <div className="aspect-[4/3] rounded-xl p-4 bg-white border border-slate-100 shadow-inner">
      <div className="text-sm text-slate-600 mb-3">Smart inbox</div>
      <ul className="space-y-2 text-sm">
        {[
          { title:"Delivery ETA confirmed", time:"2m", tone:"Action" },
          { title:"Screened spam: warranty offer", time:"7m", tone:"Spam" },
          { title:"Meeting rescheduled", time:"1h", tone:"Info" },
        ].map((m)=> (
          <li key={m.title} className="flex items-center justify-between px-3 py-2 rounded-lg border bg-white">
            <div>{m.title}</div>
            <span className="text-xs text-slate-500">{m.time}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function AnalyticsScreen(){
  return (
    <div className="aspect-[4/3] rounded-xl p-4 bg-white border border-slate-100 shadow-inner">
      <div className="text-sm text-slate-600 mb-3">Weekly insights</div>
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { k:"Calls", v:"128" },
          { k:"Answer rate", v:"86%" },
          { k:"Spam blocked", v:"42" },
        ].map((x)=> (
          <div key={x.k} className="rounded-xl p-4 bg-gradient-to-br from-amber-50 to-white border border-amber-100 shadow-inner">
            <div className="text-xs text-slate-500">{x.k}</div>
            <div className="text-xl font-semibold">{x.v}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ParallaxStats(){
  const ref = useRef(null)
  const rx = useSpring(0, { stiffness: 120, damping: 16 })
  const ry = useSpring(0, { stiffness: 120, damping: 16 })

  const onMove = (e)=>{
    const el = ref.current; if(!el) return
    const r = el.getBoundingClientRect()
    const px = (e.clientX - r.left)/r.width - .5
    const py = (e.clientY - r.top)/r.height - .5
    ry.set(px * 10); rx.set(-py * 8)
  }

  return (
    <div ref={ref} onMouseMove={onMove} onMouseLeave={()=>{rx.set(0);ry.set(0)}} className="grid place-items-center [perspective:1000px]">
      <motion.div style={{ rotateX: rx, rotateY: ry, transformStyle: "preserve-3d" }} className="w-full">
        <div className="rounded-2xl p-5 bg-white border border-slate-200 shadow-[0_20px_50px_rgba(2,6,23,0.1)]" style={{ transform: "translateZ(50px)" }}>
          <div className="text-sm text-slate-600 mb-2">Live sentiment</div>
          <div className="h-28 rounded-xl bg-gradient-to-r from-emerald-100 via-cyan-100 to-lime-100 overflow-hidden">
            <motion.div className="h-full w-1/2 bg-gradient-to-r from-emerald-400/60 to-cyan-400/60" animate={{ x: ["-10%","55%","0%"] }} transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}/>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

function FooterBlock(){
  return (
    <section className="mt-20 grid md:grid-cols-2 gap-8 items-center">
      <div className="p-6 rounded-3xl bg-white/70 backdrop-blur border border-slate-200 shadow-[0_20px_50px_rgba(2,6,23,0.1)]">
        <h3 className="text-xl font-semibold">Make it yours</h3>
        <ul className="mt-3 text-[15px] text-slate-700 list-disc pl-5 space-y-1">
          <li>Fresh palette (cyan • emerald • lime). No dark blue.</li>
          <li>Aero-style workspace window with 3D depth and sidebars.</li>
          <li>Drag, springs, parallax and in‑view microinteractions.</li>
        </ul>
      </div>
      <div className="p-6 rounded-3xl bg-gradient-to-br from-cyan-200/60 via-emerald-200/60 to-lime-200/60 border border-white shadow-[0_20px_50px_rgba(255,255,255,0.6)_inset]">
        <div className="text-[15px]">
          Want this exported as plain HTML/CSS/JS or a Flask partial? I can package both.
        </div>
      </div>
    </section>
  )
}

/* ===== New: AeroBoard (chat + right collections + left rail) ===== */
function AeroBoard(){
  return (
    <motion.div
      className="relative rounded-[28px] bg-white/80 backdrop-blur-xl border border-white/70 shadow-[0_40px_120px_rgba(2,6,23,0.12)]"
      style={{
        boxShadow: "0 50px 120px rgba(2,6,23,0.18), inset 0 1px 0 rgba(255,255,255,0.9)",
      }}
      initial={{ opacity: 0, y: 20, scale:.98 }}
      whileInView={{ opacity:1, y:0, scale:1 }}
      viewport={{ once:true, amount:.5 }}
      transition={{ type:"spring", stiffness: 120, damping: 20 }}
    >
      <div className="grid grid-cols-[60px_1fr_320px] min-h-[520px]">
        {/* Left rail */}
        <div className="border-r border-slate-200/70 p-3 flex flex-col items-center gap-3">
          <RailIcon active><i className="fa-solid fa-comment-dots"/></RailIcon>
          <RailIcon><i className="fa-solid fa-gauge"/></RailIcon>
          <RailIcon><i className="fa-solid fa-address-book"/></RailIcon>
          <RailIcon><i className="fa-solid fa-gear"/></RailIcon>
          <div className="mt-auto"><RailIcon><i className="fa-solid fa-circle-question"/></RailIcon></div>
        </div>

        {/* Center chat area */}
        <div className="relative p-8">
          <div className="absolute inset-0 pointer-events-none [mask-image:radial-gradient(70%_60%_at_50%_30%,black,transparent_75%)]"/>
          <div className="max-w-2xl mx-auto space-y-4">
            <ChatBubble who="you">
              Create a minimalist bedroom design with muted olive tones and a forest view.
            </ChatBubble>
            <CardGallery/>
            <ChatBubble>
              Here’s a concept with a floor‑to‑ceiling window and oak wood bed. Thoughts?
            </ChatBubble>
            <Composer/>
          </div>
        </div>

        {/* Right panel */}
        <div className="border-l border-slate-200/70 p-6 bg-white/60">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-medium">AI Module</div>
            <span className="px-2 py-1 text-xs rounded-lg bg-slate-900 text-white">Thinker</span>
          </div>
          <div className="text-xs text-slate-500 mb-2">Conversations</div>
          <div className="space-y-1 mb-5">
            {['How do I reset my password?','Remind me to submit the report…','What’s on my schedule today?'].map((t)=> (
              <div key={t} className="px-3 py-2 rounded-xl bg-white/80 border border-slate-200 text-sm text-slate-700 hover:shadow-sm cursor-pointer">{t}</div>
            ))}
          </div>

          <div className="text-xs text-slate-500 mb-2">Collections</div>
          <div className="space-y-3">
            <Collection label="Project Management"/>
            <Collection label="Personal Assistant" defaultOpen items={["Schedule dentist appointment…","Remind me to call Sarah at 5 PM…"]}/>
            <Collection label="Customer Support"/>
          </div>

          {/* Sub‑screens dock */}
          <div className="mt-6">
            <div className="text-xs text-slate-500 mb-2">Sub‑screens</div>
            <div className="grid grid-cols-3 gap-2">
              <SubThumb label="Dashboard" tone="from-cyan-200 to-white"/>
              <SubThumb label="Analytics" tone="from-emerald-200 to-white"/>
              <SubThumb label="Inbox" tone="from-lime-200 to-white"/>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function RailIcon({ children, active }){
  return (
    <motion.button whileTap={{ scale:.98 }} className={`size-10 grid place-items-center rounded-2xl border ${active? 'bg-slate-900 text-white border-slate-900' : 'bg-white/70 backdrop-blur border-slate-200 text-slate-700 hover:bg-white'}`}>
      <span className="text-[15px]">{children}</span>
    </motion.button>
  )
}

function ChatBubble({ children, who }){
  const me = who === 'you'
  return (
    <div className={`max-w-[78%] ${me? 'ml-auto' : ''}`}>
      <div className={`px-4 py-3 rounded-2xl border shadow-sm ${me? 'bg-cyan-50 border-cyan-100' : 'bg-white/70 backdrop-blur border-slate-200'}`}>{children}</div>
    </div>
  )
}

function CardGallery(){
  return (
    <div className="flex gap-3">
      {["from-emerald-100 to-white","from-cyan-100 to-white","from-lime-100 to-white"].map((tone,i)=> (
        <motion.div key={i} whileHover={{ y:-4 }} className={`w-40 h-28 rounded-2xl border border-slate-200 bg-gradient-to-br ${tone} shadow-inner`}/>
      ))}
    </div>
  )
}

function Composer(){
  return (
    <div className="mt-4 flex items-center gap-2 p-2 rounded-2xl bg-white/80 border border-slate-200 shadow-sm">
      <input placeholder="Ask Voxa anything…" className="flex-1 bg-transparent outline-none px-3 py-2 text-[15px]"/>
      <button className="px-3 py-2 rounded-xl bg-slate-900 text-white">Send</button>
    </div>
  )
}

function Collection({ label, defaultOpen=false, items=[] }){
  const [open,setOpen] = useState(defaultOpen)
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/80 overflow-hidden">
      <button onClick={()=>setOpen(v=>!v)} className="w-full flex items-center justify-between px-3 py-2 text-sm">
        <span>{label}</span>
        <ChevronRight className={`h-4 w-4 transition-transform ${open? 'rotate-90' : ''}`}/>
      </button>
      {open && (
        <div className="border-t border-slate-200 p-2 space-y-1">
          {items.map(it=> <div key={it} className="px-2 py-1 rounded-lg text-sm text-slate-600 hover:bg-white">{it}</div>)}
        </div>
      )}
    </div>
  )
}

function SubThumb({ label, tone }){
  return (
    <div className={`h-16 rounded-xl border border-slate-200 bg-gradient-to-br ${tone} relative overflow-hidden`}> 
      <div className="absolute inset-0 opacity-40" style={{background:"radial-gradient(65% 65% at 35% 35%, white, transparent)"}}/>
      <div className="absolute bottom-1 left-1 right-1 text-[11px] px-2 py-1 rounded-lg bg-white/70 border border-slate-200 text-slate-700">{label}</div>
    </div>
  )
}
