
import { useState } from "react";
import Phone3D from "../components/Phone3D";

export default function WhyQuellAI() {
  const [activeDemo, setActiveDemo] = useState<string | null>(null);

  const features = [
    {
      id: "intelligent",
      title: "Truly Intelligent",
      description: "Not just automated responses - contextual understanding powered by advanced AI that learns your communication patterns.",
      icon: "[AI]"
    },
    {
      id: "privacy",
      title: "Privacy-First Design",
      description: "Your data stays yours. Local processing, auto-deletion policies, and transparent AI operations.",
      icon: "[PRIV]"
    },
    {
      id: "seamless",
      title: "Seamless Integration",
      description: "Works with your existing phone system. No app switching, no workflow disruption.",
      icon: "[FLOW]"
    },
    {
      id: "adaptive",
      title: "Adaptive Learning",
      description: "Gets smarter with every interaction. Understands your priorities, preferences, and communication style.",
      icon: "[LEARN]"
    }
  ];

  const comparisons = [
    {
      aspect: "Call Handling",
      others: "Generic voicemail or basic IVR",
      quellai: "Context-aware AI conversations with natural language understanding"
    },
    {
      aspect: "Spam Protection",
      others: "Simple blocklists",
      quellai: "Multi-layer ML detection with reputation scoring and behavioral analysis"
    },
    {
      aspect: "Privacy",
      others: "Cloud storage, unclear data usage",
      quellai: "Local-first, auto-deletion, transparent AI operations"
    },
    {
      aspect: "Integration",
      others: "Separate apps and workflows",
      quellai: "Seamless phone system integration, no context switching"
    }
  ];

  return (
    <div className="why-page">
      {/* Hero Section */}
      <section className="section-padding" style={{ textAlign: 'center' }}>
        <h1 className="headline" style={{ fontSize: 'clamp(2.5rem, 5vw, 4rem)', marginBottom: '24px' }}>
          Designed for Intelligence.
        </h1>
        <p className="subheadline" style={{ fontSize: '1.25rem', maxWidth: '800px', margin: '0 auto 48px' }}>
          Quell-AI isn't just another call management tool. It's a fundamental rethinking of how AI can enhance human communication without compromising privacy or control.
        </p>
        
        <div style={{ maxWidth: '500px', margin: '0 auto' }}>
          <Phone3D />
        </div>
      </section>

      {/* What Makes Us Different */}
      <section className="section-padding" style={{ background: 'linear-gradient(180deg, white 0%, #f9f9f9 100%)' }}>
        <h2 style={{ fontSize: '2rem', textAlign: 'center', marginBottom: '48px' }}>
          What Makes Quell-AI Different
        </h2>
        
        <div className="features-grid" style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
          gap: '32px',
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          {features.map((feature) => (
            <div 
              key={feature.id}
              className="feature-card"
              onMouseEnter={() => setActiveDemo(feature.id)}
              onMouseLeave={() => setActiveDemo(null)}
              style={{
                padding: '32px',
                background: 'white',
                borderRadius: '12px',
                border: '1px solid #e0e0e0',
                cursor: 'pointer',
                transform: activeDemo === feature.id ? 'scale(1.02)' : 'scale(1)',
                boxShadow: activeDemo === feature.id 
                  ? '0 8px 24px rgba(168, 223, 142, 0.2)' 
                  : '0 2px 8px rgba(0, 0, 0, 0.05)',
                transition: 'all 0.25s ease'
              }}
            >
              <div style={{ fontSize: '3rem', marginBottom: '16px' }}>{feature.icon}</div>
              <h3 style={{ fontSize: '1.5rem', marginBottom: '12px' }}>{feature.title}</h3>
              <p style={{ color: '#666', lineHeight: '1.6' }}>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Comparison Table */}
      <section className="section-padding">
        <h2 style={{ fontSize: '2rem', textAlign: 'center', marginBottom: '48px' }}>
          Quell-AI vs. Traditional Solutions
        </h2>
        
        <div style={{ maxWidth: '900px', margin: '0 auto', overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            background: 'white',
            borderRadius: '12px',
            overflow: 'hidden',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)'
          }}>
            <thead>
              <tr style={{ background: '#f9f9f9' }}>
                <th style={{ padding: '20px', textAlign: 'left', fontWeight: '600' }}>Feature</th>
                <th style={{ padding: '20px', textAlign: 'left', fontWeight: '600' }}>Traditional Tools</th>
                <th style={{ padding: '20px', textAlign: 'left', fontWeight: '600', color: 'var(--accent-pastel-green)' }}>Quell-AI</th>
              </tr>
            </thead>
            <tbody>
              {comparisons.map((comp, idx) => (
                <tr key={idx} style={{ borderTop: '1px solid #e0e0e0' }}>
                  <td style={{ padding: '20px', fontWeight: '500' }}>{comp.aspect}</td>
                  <td style={{ padding: '20px', color: '#666' }}>{comp.others}</td>
                  <td style={{ padding: '20px', color: '#1a1a1a', fontWeight: '500' }}>{comp.quellai}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Interactive Demo Section */}
      <section className="section-padding" style={{ background: 'linear-gradient(180deg, #f9f9f9 0%, white 100%)' }}>
        <h2 style={{ fontSize: '2rem', textAlign: 'center', marginBottom: '24px' }}>
          Experience It Yourself
        </h2>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '48px', maxWidth: '600px', margin: '0 auto 48px' }}>
          Try these interactive demos to see how Quell-AI handles real-world scenarios.
        </p>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '24px',
          maxWidth: '1000px',
          margin: '0 auto'
        }}>
          <DemoCard 
            title="Smart Call Screening"
            description="See how AI decides which calls need your attention"
            demoType="screening"
          />
          <DemoCard 
            title="Context Memory"
            description="Watch AI recall previous conversation context"
            demoType="memory"
          />
          <DemoCard 
            title="Spam Detection"
            description="Experience multi-layer spam filtering in action"
            demoType="spam"
          />
        </div>
      </section>

      {/* CTA Section */}
      <section className="section-padding" style={{ textAlign: 'center', paddingTop: '80px', paddingBottom: '80px' }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: '24px' }}>
          Ready to Transform Your Communication?
        </h2>
        <p style={{ fontSize: '1.25rem', color: '#666', marginBottom: '40px', maxWidth: '700px', margin: '0 auto 40px' }}>
          Join the waitlist and be among the first to experience intelligent call management.
        </p>
        <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button className="button-engage" style={{ fontSize: '1.1rem', padding: '14px 32px' }}>
            Join Waitlist
          </button>
          <button className="button-outline" style={{ fontSize: '1.1rem', padding: '14px 32px' }}>
            Book a Demo
          </button>
        </div>
      </section>
    </div>
  );
}

// Demo Card Component
function DemoCard({ title, description, demoType }: { title: string; description: string; demoType: string }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const demoLabel = demoType.replace(/[-_]/g, " ");
  const friendlyLabel = demoLabel.replace(/\b\w/g, (char) => char.toUpperCase());

  return (
    <div
      data-demo-type={demoType}
      aria-label={`Interactive demo: ${friendlyLabel}`}
      style={{
        padding: '24px',
        background: 'white',
        borderRadius: '12px',
        border: '1px solid #e0e0e0',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
        transition: 'all 0.25s ease',
        cursor: 'pointer'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.05)';
      }}
      onClick={() => setIsPlaying(!isPlaying)}
    >
      <div style={{
        width: '100%',
        height: '200px',
        background: '#f0f0f0',
        borderRadius: '8px',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {!isPlaying ? (
          <div style={{
            width: '60px',
            height: '60px',
            background: 'var(--accent-pastel-green)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.9rem',
            fontWeight: 600,
            letterSpacing: '0.05em'
          }}>
            Play
          </div>
        ) : (
          <div style={{
            width: '100%',
            height: '100%',
            background: 'linear-gradient(135deg, var(--accent-pastel-green) 0%, #7ec96f 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '18px',
            fontWeight: 500
          }}>
            Demo Playing: {friendlyLabel}
          </div>
        )}
      </div>
      <h3 style={{ fontSize: '1.25rem', marginBottom: '8px' }}>{title}</h3>
      <p style={{ color: '#666', fontSize: '0.95rem' }}>{description}</p>
    </div>
  );
}
