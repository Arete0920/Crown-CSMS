import CrownCard from '../crown/CrownCard.jsx';

export default function HealthRingCard({ title, percent = 88, subtitle, detail }) {
  const bounded = Math.max(0, Math.min(100, percent));
  const degrees = Math.round((bounded / 100) * 360);

  return (
    <CrownCard title={title}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div
          style={{
            position: 'relative',
            width: 96,
            height: 96,
            borderRadius: '50%',
            background: `conic-gradient(var(--crown-brand) ${degrees}deg, var(--crown-surface-2) ${degrees}deg)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              background: 'var(--crown-surface)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 900,
              color: 'var(--crown-brand)',
            }}
          >
            {bounded}%
          </div>
        </div>

        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--crown-ink)' }}>{subtitle}</div>
          <div style={{ marginTop: 4, fontSize: 12, color: 'var(--crown-muted)' }}>
            Weighted institutional health
          </div>
        </div>
      </div>

      <p style={{ marginTop: 12, marginBottom: 0, fontSize: 12, color: 'var(--crown-muted)', lineHeight: 1.6 }}>
        {detail}
      </p>
    </CrownCard>
  );
}
