import React from 'react';
import HeroSection from './components/HeroSection';
import { SALESGENIUS_URL, PLOTSENSE_URL } from './config';

function LauncherCard({ icon, color, title, subtitle, description, features, url, btnLabel, status }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 20,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      transition: 'transform 0.2s, box-shadow 0.2s',
    }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 16px 48px rgba(0,0,0,0.5)'; }}
      onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}
    >
      {/* Card Top Banner */}
      <div style={{
        background: color,
        padding: '40px 36px 32px',
        display: 'flex', flexDirection: 'column', gap: 16,
      }}>
        <div>
          <div style={{ fontSize: 26, fontWeight: 800, color: '#fff', letterSpacing: '-0.5px' }}>{title}</div>
          <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 4 }}>{subtitle}</div>
        </div>
      </div>

      {/* Card Body */}
      <div style={{ padding: '28px 36px', flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
        <p style={{ color: 'var(--text-muted)', fontSize: 15, lineHeight: 1.6 }}>{description}</p>

        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {features.map((f, i) => (
            <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, color: 'var(--text)' }}>
              <span style={{ color: '#34d399', flexShrink: 0 }}>✓</span> {f}
            </li>
          ))}
        </ul>

        {/* Server Status Badge */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'var(--surface2)', borderRadius: 8, padding: '8px 14px',
          border: '1px solid var(--border)', fontSize: 13,
        }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#34d399', boxShadow: '0 0 6px #34d399', display: 'inline-block' }} />
          <span style={{ color: 'var(--text-muted)' }}>Server:</span>
          <code style={{ color: 'var(--accent2)', fontFamily: 'monospace' }}>{url}</code>
          <span style={{ marginLeft: 'auto', color: '#34d399', fontWeight: 600 }}>{status}</span>
        </div>

        {/* Launch Button */}
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
            padding: '14px 24px', borderRadius: 12,
            background: color, color: '#fff',
            fontWeight: 700, fontSize: 16, textDecoration: 'none',
            transition: 'opacity 0.2s, transform 0.2s',
            boxShadow: `0 8px 24px rgba(0,0,0,0.3)`,
          }}
          onMouseEnter={e => { e.currentTarget.style.opacity = '0.88'; e.currentTarget.style.transform = 'scale(1.01)'; }}
          onMouseLeave={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.transform = ''; }}
        >
          {btnLabel} ↗
        </a>
      </div>
    </div>
  );
}

export default function App() {
  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <>
      {/* Navbar */}
      <nav className="navbar">
        <div className="container navbar-inner">
          <div className="logo">
            <div className="logo-icon">S</div>
            <span className="logo-name">Sales<span>Genius</span></span>
          </div>
          <div className="nav-tabs">
            <a href={SALESGENIUS_URL} target="_blank" rel="noopener noreferrer" className="nav-tab">
              SalesGenius ↗
            </a>
            <a href={PLOTSENSE_URL} target="_blank" rel="noopener noreferrer" className="nav-tab">
              PlotSense ↗
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <HeroSection onScrollTo={scrollTo} />

      {/* Launcher Cards */}
      <section id="services" className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <div className="section-header" style={{ textAlign: 'center' }}>
            <h2>Choose Your Tool</h2>
            <p>Both services are running locally. Click to open them.</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 28 }}>
            <LauncherCard
              color="linear-gradient(135deg, #6366f1, #818cf8)"
              title="SalesGenius"
              subtitle="AI Sales Intelligence Agent"
              description="Engage prospects, qualify leads with real Financial DNA benchmarks, and receive personalized recommendations powered by a 3-agent AI chain."
              features={[
                'Analyzer → Validator → Sales Agent pipeline',
                'Real-time Financial DNA benchmarks',
                'Live web intelligence via Tavily',
                'Dynamic client profile tracker',
                'Intelligence Trace visibility',
              ]}
              url={SALESGENIUS_URL}
              btnLabel="Open SalesGenius"
              status="Running"
            />

            <LauncherCard
              color="linear-gradient(135deg, #06b6d4, #22d3ee)"
              title="PlotSense"
              subtitle="AI Data Analytics Dashboard"
              description="Upload any CSV dataset and get AI-generated chart recommendations, automated visualizations, and plain-language insights instantly."
              features={[
                'Drag-and-drop CSV upload',
                'AI chart type recommendations',
                'Automated plot generation',
                'Plain-language AI explanations',
                'Sector-aware analytics',
              ]}
              url={PLOTSENSE_URL}
              btnLabel="Open PlotSense"
              status="Running"
            />
          </div>

          {/* Architecture Note */}
          <div style={{
            marginTop: 48, padding: '28px 36px',
            background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 16,
            display: 'flex', alignItems: 'flex-start', gap: 20,
          }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--accent-glow)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, color: 'var(--accent)', fontSize: 18 }}>AI</div>
            <div>
              <div style={{ fontWeight: 700, marginBottom: 8, fontSize: 16 }}>Multi-Agent Architecture</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.7 }}>
                SalesGenius runs a <strong style={{ color: 'var(--text)' }}>3-agent sequential chain</strong>:{' '}
                the <strong style={{ color: '#6366f1' }}>Analyzer</strong> gates irrelevant queries →{' '}
                the <strong style={{ color: '#818cf8' }}>Validator</strong> structures the intent into a sales brief →{' '}
                the <strong style={{ color: '#22d3ee' }}>Expert Closer</strong> generates data-backed recommendations.
                PlotSense adds a parallel <strong style={{ color: 'var(--text)' }}>analytics pipeline</strong> powered by the PlotSense library.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          Built for <span>Hackathon · LunarHack</span> ·{' '}
          SalesGenius · PlotSense · Unified Dashboard
        </div>
      </footer>
    </>
  );
}
