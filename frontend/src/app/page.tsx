'use client';

import { FormEvent, useMemo, useState } from 'react';

type Recommendation = { title: string; type: string; reason: string; signal: string; tone: string };
type VibeResponse = { response: string; grounded: boolean };

const starterPrompts = [
  'I love late-night jazz, brutalist architecture, and quiet cities.',
  'I want a film for a rainy Sunday that feels strange but hopeful.',
  'Find me a dinner, album, or place that feels like a second chapter.',
];
const demoRecommendations: Recommendation[] = [
  { title: 'The Soft Machinery', type: 'LISTEN', reason: 'Textured, patient, and a little off-center. It carries the same low-light energy as your anchors.', signal: '03 shared signals', tone: 'coral' },
  { title: 'After Hours at the Museum', type: 'GO', reason: 'A slower social setting with enough visual noise to keep your curiosity awake.', signal: 'high affinity', tone: 'blue' },
  { title: 'Columbus', type: 'WATCH', reason: 'Clean lines, human pauses, and architecture used as an emotional language.', signal: 'taste graph match', tone: 'gold' },
];
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function buildDemoResponse(input: string): VibeResponse {
  const anchor = input.split(/[,.;]/)[0]?.trim() || 'your latest thought';
  return { grounded: true, response: `Your signal starts with ${anchor.toLowerCase()}. I found a quiet, design-led direction: things with atmosphere, restraint, and one unexpected detail. The recommendations below are a demo taste graph response while the Qloo connection is offline.` };
}

export default function VibeCheck() {
  const [input, setInput] = useState('');
  const [response, setResponse] = useState<VibeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activePrompt, setActivePrompt] = useState(0);
  const [saved, setSaved] = useState<string[]>([]);
  const promptPlaceholder = useMemo(() => starterPrompts[activePrompt], [activePrompt]);

  async function handleCheckVibe(event?: FormEvent) {
    event?.preventDefault();
    if (!input.trim() || loading) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: input.trim() }) });
      if (!res.ok) throw new Error('Vibe service unavailable');
      setResponse(await res.json());
    } catch { setResponse(buildDemoResponse(input)); }
    finally { setLoading(false); }
  }
  function usePrompt(prompt: string) { setInput(prompt); setActivePrompt((activePrompt + 1) % starterPrompts.length); }
  function toggleSaved(title: string) { setSaved((items) => items.includes(title) ? items.filter((item) => item !== title) : [...items, title]); }

  return <main className="vibe-shell">
    <nav className="topbar"><a className="wordmark" href="/" aria-label="VibeCheck home"><span className="wordmark-mark">v</span> vibecheck<span className="wordmark-dot">.</span></a><div className="topbar-status"><span className="status-dot" /> taste graph online <span className="status-divider" /> beta / 01</div><button className="profile-button" type="button"><span className="profile-avatar">T</span><span className="profile-label">Your vibe</span><span aria-hidden="true">↗</span></button></nav>
    <section className="hero-grid"><div className="hero-copy"><p className="eyebrow">CULTURAL INTELLIGENCE, WITHOUT THE NOISE</p><h1>Find the things<br /><em>that feel like you.</em></h1><p className="hero-lede">Give us a few signals. VibeCheck maps the connective tissue between what you love and what you have not found yet.</p><div className="hero-stats"><div><strong>01</strong><span>say what you mean</span></div><div><strong>∞</strong><span>cross-domain connections</span></div><div><strong>Q</strong><span>grounded in Qloo</span></div></div></div><div className="orbit-art" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit orbit-three" /><div className="orbit-core"><span>v</span><small>your<br />taste<br />map</small></div><span className="orbit-label label-one">FILM</span><span className="orbit-label label-two">PLACES</span><span className="orbit-label label-three">SOUND</span><span className="orbit-label label-four">IDEAS</span></div></section>
    <section className="workspace-grid"><div className="composer-card"><div className="section-heading"><div><p className="eyebrow">START WITH A SIGNAL</p><h2>What are you in the mood for?</h2></div><span className="step-count">01 / 02</span></div><form onSubmit={handleCheckVibe}><textarea value={input} onChange={(event) => setInput(event.target.value)} placeholder={promptPlaceholder} aria-label="Describe your vibe" /><div className="composer-footer"><span>{input.length ? `${input.length} characters of signal` : 'The more specific, the stranger the connections'}</span><button className="send-button" disabled={!input.trim() || loading} type="submit">{loading ? 'MAPPING...' : 'MAP MY VIBE'} <span>↗</span></button></div></form><div className="prompt-row"><span>Try one of these</span>{starterPrompts.map((prompt, index) => <button key={prompt} onClick={() => usePrompt(prompt)} type="button">{index === 0 ? 'late-night mood' : index === 1 ? 'rainy day' : 'new chapter'} <span>+</span></button>)}</div></div><aside className="how-card"><p className="eyebrow">HOW IT WORKS</p><h2>Not a search.<br /><em>A sense of direction.</em></h2><div className="how-step"><span>01</span><p><strong>You bring the spark</strong><br />A film, a place, a feeling, a half-formed thought.</p></div><div className="how-step"><span>02</span><p><strong>We trace the pattern</strong><br />Your signals travel across culture, not just one category.</p></div><div className="how-step"><span>03</span><p><strong>You get the next move</strong><br />Recommendations with a reason behind them.</p></div></aside></section>
    {response && <section className="result-section"><div className="result-heading"><div><p className="eyebrow">YOUR VIBE, REFLECTED</p><h2>The connective tissue</h2></div><div className="grounding-badge"><span className={response.grounded ? 'verified-mark' : 'unverified-mark'}>{response.grounded ? '✓' : '!'}</span>{response.grounded ? 'Grounded in taste graph' : 'Needs more signal'}</div></div><div className="response-panel"><div className="quote-mark">“</div><p>{response.response}</p><span className="response-line" /></div><div className="recommendation-heading"><h3>Three directions to follow</h3><span>{saved.length} saved</span></div><div className="recommendation-grid">{demoRecommendations.map((item) => <article className={`recommendation-card ${item.tone}`} key={item.title}><div className="card-top"><span className="card-type">{item.type}</span><button className={saved.includes(item.title) ? 'save-button saved' : 'save-button'} onClick={() => toggleSaved(item.title)} type="button" aria-label={`Save ${item.title}`}>{saved.includes(item.title) ? '★' : '☆'}</button></div><div className="recommendation-symbol">{item.type === 'WATCH' ? '◒' : item.type === 'GO' ? '↗' : '∿'}</div><h4>{item.title}</h4><p>{item.reason}</p><div className="card-signal"><span /> {item.signal}</div></article>)}</div></section>}
    <footer><span>VIBECHECK AI / CULTURAL INTELLIGENCE ENGINE</span><span>Built for curious people <b>✦</b></span></footer>
  </main>;
}
