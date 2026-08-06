import CrownCard from './CrownCard.jsx';

/**
 * CrownMetricCard – single KPI tile used in the top metric row.
 *
 * Props:
 *   label – metric name (small, muted)
 *   value – primary display value (large, bold)
 *   hint  – secondary note below the value (small, muted)
 */
export default function CrownMetricCard({ label, value, hint }) {
  return (
    <CrownCard>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div
          style={{ fontSize: 12, color: 'var(--crown-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.4 }}
        >
          {label}
        </div>
        <div style={{ fontSize: 22, fontWeight: 900, letterSpacing: 0.2 }}>
          {value}
        </div>
        {hint ? (
          <div style={{ fontSize: 12, color: 'var(--crown-muted)' }}>{hint}</div>
        ) : null}
      </div>
    </CrownCard>
  );
}
