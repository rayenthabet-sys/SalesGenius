import React from 'react';

export default function HeroSection({ onScrollTo }) {
  return (
    <section className="hero">
      <div className="container">
        <div className="hero-badge">
          <span className="dot" />
          Live AI · Multi-Agent System
        </div>
        <h1>
          Your AI-Powered<br />
          <span className="gradient-text">Sales Intelligence</span> Platform
        </h1>
        <p>
          Qualify leads, decode Financial DNA, and generate data-backed
          analytics — all from a single unified dashboard.
        </p>
        <div className="flex items-center gap-2" style={{ justifyContent: 'center', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => onScrollTo('services')}>
            Explore Tools
          </button>
        </div>
        <div className="hero-stats">
          <div className="hero-stat">
            <div className="value">3</div>
            <div className="label">AI Agents in Chain</div>
          </div>
          <div className="hero-stat">
            <div className="value">5</div>
            <div className="label">Industry Sectors</div>
          </div>
          <div className="hero-stat">
            <div className="value">∞</div>
            <div className="label">Conversation Turns</div>
          </div>
          <div className="hero-stat">
            <div className="value">Live</div>
            <div className="label">Web Intelligence</div>
          </div>
        </div>
      </div>
    </section>
  );
}
