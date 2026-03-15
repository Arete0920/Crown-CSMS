import { useState } from 'react';
import CrownCard from '../crown/CrownCard.jsx';

export default function FlipMetricCard({
  title,
  value,
  trend,
  definition,
  sources = [],
  links = [],
}) {
  const [flipped, setFlipped] = useState(false);

  if (!flipped) {
    return (
      <CrownCard>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 12, color: 'var(--crown-muted)', fontWeight: 700 }}>{title}</div>
            <div style={{ fontSize: 30, fontWeight: 900, color: 'var(--crown-brand)', marginTop: 8 }}>{value}</div>
            <div style={{ fontSize: 12, color: 'var(--crown-ok)', marginTop: 8 }}>{trend}</div>
          </div>
          <button className="crown-btn" style={{ fontSize: 12 }} onClick={() => setFlipped(true)}>
            Info
          </button>
        </div>
        <div style={{ height: 4, width: 56, borderRadius: 999, background: 'var(--crown-accent)', marginTop: 10 }} />
      </CrownCard>
    );
  }

  return (
    <CrownCard title={`${title} Definition`} right={<button className="crown-btn" style={{ fontSize: 12 }} onClick={() => setFlipped(false)}>Back</button>}>
      <p style={{ fontSize: 12, color: 'var(--crown-muted)', lineHeight: 1.6, marginTop: 0 }}>{definition}</p>

      <div style={{ marginTop: 8 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: 'var(--crown-muted)', letterSpacing: 0.5, textTransform: 'uppercase' }}>
          Source Data
        </div>
        <ul style={{ margin: '6px 0 0 0', paddingLeft: 16, fontSize: 12, color: 'var(--crown-ink)' }}>
          {sources.map((source) => (
            <li key={source}>{source}</li>
          ))}
        </ul>
      </div>

      <div style={{ marginTop: 10 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: 'var(--crown-muted)', letterSpacing: 0.5, textTransform: 'uppercase' }}>
          Links
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
          {links.map((link) => (
            <button key={link} className="crown-btn" style={{ fontSize: 11, padding: '6px 8px' }}>
              {link}
            </button>
          ))}
        </div>
      </div>
    </CrownCard>
  );
}
