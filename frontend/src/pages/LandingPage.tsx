// import Phone3D from "../components/Phone3D"; // archived
import { useAuth } from "../components/AuthProvider";

export default function LandingPage() {
  const { engage } = useAuth();
  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero section-padding" style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '48px',
        alignItems: 'center'
      }}>
        <div>
          <h1 className="headline" style={{ fontSize: 'clamp(2.5rem, 5vw, 3.5rem)', marginBottom: '24px' }}>
            Your communicator copilot that respects every call
          </h1>
          <p className="subheadline" style={{ fontSize: '1.25rem', marginBottom: '32px', color: '#666' }}>
            Quell-AI filters the noise, captures the signal, and keeps your attention on high-impact work.
          </p>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <button className="button-engage" onClick={engage}>Engage with the Application</button>
          </div>
        </div>
        {/* Phone3D archived */}
      </section>

      {/* Mission Section */}
      <section className="section-padding" style={{ background: '#f9f9f9' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '2rem', marginBottom: '24px' }}>Our Mission</h2>
          <p style={{ fontSize: '1.1rem', lineHeight: '1.8', color: '#666' }}>
            We believe communication should enhance productivity, not interrupt it. Quell-AI is built on the principle that AI should serve as an intelligent assistant that filters spam, manages routine interactions, and makes sure you never miss what matters.
          </p>
        </div>
      </section>

      {/* Core Values */}
      <section className="section-padding">
        <h2 style={{ fontSize: '2rem', textAlign: 'center', marginBottom: '48px' }}>Why Choose Quell-AI</h2>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
          gap: '32px'
        }}>
          {[
            {
              title: "Call Screening",
              description: "Answer the right conversations - Quell-AI politely handles the rest.",
              icon: "[Call]"
            },
            {
              title: "Memory on Tap",
              description: "Every call summarized instantly with action items you can trust.",
              icon: "[Memory]"
            },
            {
              title: "Trusted Boundaries",
              description: "Respect priority contacts and protect your evenings without missing a beat.",
              icon: "[Trust]"
            }
          ].map((feature, idx) => (
            <div key={idx} style={{
              padding: '32px',
              background: 'white',
              borderRadius: '12px',
              border: '1px solid #e0e0e0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
              transition: 'all 0.25s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.05)';
            }}
            >
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>{feature.icon}</div>
              <h3 style={{ fontSize: '1.5rem', marginBottom: '12px' }}>{feature.title}</h3>
              <p style={{ color: '#666', lineHeight: '1.6' }}>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Story Gallery Placeholder */}
      <section className="section-padding" style={{ background: '#f9f9f9' }}>
        <h2 style={{ fontSize: '2rem', textAlign: 'center', marginBottom: '48px' }}>How It Works</h2>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '24px',
          maxWidth: '1000px',
          margin: '0 auto'
        }}>
          {[
            { step: "1", title: "Connect", desc: "Link your phone system in minutes" },
            { step: "2", title: "Configure", desc: "Set your preferences and priorities" },
            { step: "3", title: "Relax", desc: "Let AI handle the noise" }
          ].map((item) => (
            <div key={item.step} style={{
              padding: '24px',
              background: 'white',
              borderRadius: '12px',
              textAlign: 'center',
              border: '1px solid #e0e0e0'
            }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'var(--accent-pastel-green)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                fontWeight: '600',
                margin: '0 auto 16px'
              }}>
                {item.step}
              </div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '8px' }}>{item.title}</h3>
              <p style={{ color: '#666' }}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}





