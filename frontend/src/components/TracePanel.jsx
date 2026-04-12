import React, { useState } from 'react';

export default function TracePanel({ trace }) {
  const [open, setOpen] = useState(false);

  const analyzer = trace?.analyzer || null;
  const validator = trace?.validator || null;

  if (!analyzer && !validator) return null;

  return (
    <div className="card" style={{ marginTop: 16 }}>
      <div
        className="card-header"
        style={{ cursor: 'pointer', userSelect: 'none' }}
        onClick={() => setOpen(o => !o)}
      >
        <div className="card-title">
          <div className="card-icon">🕵️</div>
          Intelligence Trace
        </div>
        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          {open ? '▲ Hide' : '▼ Show'}
        </span>
      </div>
      {open && (
        <div className="trace-panel">
          {analyzer && (
            <div className="trace-step">
              <div className="trace-step-header">
                <span className="trace-step-badge">🛡️ Analyzer</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Gatekeeper decision</span>
              </div>
              <div className="trace-step-content">{analyzer}</div>
            </div>
          )}
          {validator && (
            <div className="trace-step">
              <div className="trace-step-header">
                <span className="trace-step-badge">📝 Validator</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Context refinement</span>
              </div>
              <div className="trace-step-content">{validator}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
