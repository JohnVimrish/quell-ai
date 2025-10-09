import HeroPhone from "../sections/HeroPhone";
import StoryGallery from "../sections/StoryGallery";

export default function LandingPage() {
  return (
    <div className="landing-page">
      <section className="hero section-padding">
        <div>
          <h1 className="headline">Your communicator copilot that respects every call</h1>
          <p className="subheadline">
            Quell-AI filters the noise, captures the signal, and keeps your attention on high-impact work.
          </p>
          <div className="hero-actions">
            <button className="button-primary">Start free trial</button>
            <button className="button-outline">Book a demo</button>
          </div>
        </div>
        <HeroPhone />
      </section>

      <section className="section-padding glass-panel">
        <h2>Why choose Quell-AI</h2>
        <ul className="features-grid">
          <li className="feature-card">
            <h3>Call Screening</h3>
            <p>Answer the right conversations—Quell politely handles the rest.</p>
          </li>
          <li className="feature-card">
            <h3>Memory on Tap</h3>
            <p>Every call summarized instantly with action items you can trust.</p>
          </li>
          <li className="feature-card">
            <h3>Trusted Boundaries</h3>
            <p>Respect priority contacts and protect your evenings without missing a beat.</p>
          </li>
        </ul>
      </section>

      <StoryGallery />
    </div>
  );
}



