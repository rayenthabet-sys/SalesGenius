import React from 'react';
import ReactMarkdown from 'react-markdown';

/** Shows the Dynamic Client Profile with non-null fields only */
export function ProfileCard({ profileJson, dna }) {
  let profile = {};
  try {
    profile = typeof profileJson === 'string' ? JSON.parse(profileJson) : (profileJson || {});
  } catch { /* ignore parse errors */ }

  const labelMap = {
    company_name: 'Company', sector: 'Sector', sme_size: 'Size',
    annual_revenue: 'Revenue', financial_health: 'Financial Health',
    pain_points: 'Pain Points', goals: 'Goals', budget: 'Budget',
    decision_timeline: 'Timeline',
  };

  // Parse simple DNA string from Gradio (fallback)
  const dnaLines = typeof dna === 'string'
    ? dna.replace(/\*\*/g, '').split('\n').filter(l => l.startsWith('-'))
    : [];

  return (
    <div className="card" style={{ height: '100%' }}>
      <div className="card-header">
        <div className="card-title">
          <div className="card-icon">👤</div>
          Client Profile
        </div>
      </div>
      <div className="card-body profile-grid">
        {Object.entries(labelMap).map(([key, label]) => {
          const val = profile[key];
          const display = Array.isArray(val) ? val.join(', ') : val;
          return (
            <div key={key} className="profile-field">
              <div className="field-label">{label}</div>
              <div className={`field-value ${!display ? 'null-value' : ''}`}>
                {display || '—'}
              </div>
            </div>
          );
        })}
      </div>
      {dnaLines.length > 0 && (
        <>
          <div className="card-header" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="card-title"><div className="card-icon">🧬</div>Financial DNA</div>
          </div>
          <div className="dna-bars">
            {dnaLines.map((line, i) => {
              // Parse "- Literacy: 3.3/5"
              const match = line.match(/[-•]\s*(.+?):\s*([\d.]+)\s*\/\s*5/);
              if (!match) return null;
              const [, name, score] = match;
              const pct = (parseFloat(score) / 5) * 100;
              return (
                <div key={i} className="dna-row">
                  <span className="dna-label">{name.trim()}</span>
                  <div className="dna-bar-bg"><div className="dna-bar-fill" style={{ width: `${pct}%` }} /></div>
                  <span className="dna-value">{score}</span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

/** Shows the agent's recommendations as a polished list */
export function RecommendationsCard({ recommendations }) {
  if (!recommendations) return null;
  const lines = typeof recommendations === 'string'
    ? recommendations.split('\n').filter(l => l.trim() && !l.startsWith('#'))
    : [];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title"><div className="card-icon">💡</div>Recommendations</div>
      </div>
      <div className="card-body">
        {lines.length === 0 || lines.every(l => l.trim() === 'None') ? (
          <p className="text-muted">Chat to receive recommendations.</p>
        ) : (
          <ul className="recs-list">
            {lines
              .filter(l => l.trim() !== 'None')
              .map((l, i) => (
                <li key={i} className="recs-item">{l.replace(/^[-•*]\s*/, '')}</li>
              ))}
          </ul>
        )}
      </div>
    </div>
  );
}
