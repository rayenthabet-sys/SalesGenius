import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendChatMessage } from '../api/salesGenius';
import { ProfileCard, RecommendationsCard } from './ProfileCard';
import TracePanel from './TracePanel';
import { SECTORS, COMPANY_SIZES } from '../config';

export default function ChatPanel() {
  const [messages, setMessages] = useState([]); // [{role, content}]
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [companyName, setCompanyName] = useState('');
  const [sector, setSector] = useState('');
  const [size, setSize] = useState('');
  const [useSearch, setUseSearch] = useState(true);

  // Live Intel state
  const [profileJson, setProfileJson] = useState('{}');
  const [dna, setDna] = useState('');
  const [recommendations, setRecommendations] = useState('');
  const [trace, setTrace] = useState(null);

  const bottomRef = useRef(null);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput('');
    setError(null);

    const userMsg = { role: 'user', content: text };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setLoading(true);

    try {
      const result = await sendChatMessage({
        message: text,
        history: messages, // pass existing history
        companyName,
        sector,
        size,
        useSearch,
      });

      setMessages(result.newHistory || [...nextMessages, { role: 'assistant', content: 'No response received.' }]);
      setDna(result.dna || '');
      setProfileJson(result.profileJson || '{}');
      setRecommendations(result.recommendations || '');
      setTrace(result.trace || null);
    } catch (err) {
      setError(err.message);
      setMessages([...nextMessages, { role: 'assistant', content: `⚠️ Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setProfileJson('{}');
    setDna('');
    setRecommendations('');
    setTrace(null);
    setError(null);
  };

  return (
    <div className="chat-layout">
      {/* Left: Prospect Details */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title"><div className="card-icon">🏢</div>Prospect Details</div>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="form-group">
              <label className="form-label">Company Name</label>
              <input
                className="form-control"
                placeholder="e.g. TechFlow Solutions"
                value={companyName}
                onChange={e => setCompanyName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Sector</label>
              <select className="form-control" value={sector} onChange={e => setSector(e.target.value)}>
                <option value="">Select sector…</option>
                {SECTORS.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Company Size</label>
              <select className="form-control" value={size} onChange={e => setSize(e.target.value)}>
                <option value="">Select size…</option>
                {COMPANY_SIZES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div className="toggle-row">
              <input type="checkbox" className="toggle-input" checked={useSearch} onChange={e => setUseSearch(e.target.checked)} id="webSearch" />
              <label htmlFor="webSearch">Use Web Search (Tavily)</label>
            </div>
          </div>
        </div>

        <button className="btn btn-secondary full-width" onClick={handleReset}>🔄 Reset Conversation</button>
      </div>

      {/* Center: Chat */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', minHeight: 540 }}>
        <div className="card-header">
          <div className="card-title">
            <div className="card-icon">💬</div>SalesGenius Chat
          </div>
          <div className="flex items-center gap-2">
            <div className={`status-dot ${loading ? '' : 'offline'}`} style={loading ? {} : { background: 'var(--success)', boxShadow: '0 0 6px var(--success)' }} />
            <span className="text-muted">{loading ? 'Thinking…' : 'Ready'}</span>
          </div>
        </div>

        <div className="chat-messages" style={{ flex: 1 }}>
          {messages.length === 0 ? (
            <div className="chat-empty">
              <span className="icon">🤖</span>
              <p>Start a conversation about your prospect or business challenge.</p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                {msg.role === 'assistant'
                  ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                  : msg.content}
              </div>
            ))
          )}
          {loading && (
            <div className="chat-bubble assistant flex items-center gap-2">
              <div className="spinner" />
              <span style={{ color: 'var(--text-muted)' }}>Analyzing your request…</span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="chat-input-row">
          <input
            placeholder="Type your message and press Enter…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            disabled={loading}
          />
          <button className="btn btn-primary" onClick={handleSend} disabled={loading || !input.trim()}>
            {loading ? <span className="spinner" /> : 'Send →'}
          </button>
        </div>
      </div>

      {/* Right: Live Intel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <ProfileCard profileJson={profileJson} dna={dna} />
        <RecommendationsCard recommendations={recommendations} />
        <TracePanel trace={trace} />
      </div>
    </div>
  );
}
