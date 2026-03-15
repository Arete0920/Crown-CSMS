import CrownCard from '../crown/CrownCard.jsx';

export default function KpiCard({ title, value, trend, icon, tone = 'default' }) {
  const trendColor =
    tone === 'good'
      ? 'var(--crown-ok)'
      : tone === 'warn'
      ? 'var(--crown-warn)'
      : tone === 'bad'
      ? 'var(--crown-danger)'
      : 'var(--crown-muted)';

  return (
    <CrownCard>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 12, color: 'var(--crown-muted)', fontWeight: 700 }}>{title}</span>
        <span style={{ fontSize: 16 }}>{icon}</span>
      </div>
      <div style={{ fontSize: 30, fontWeight: 900, color: 'var(--crown-brand)', marginTop: 10 }}>{value}</div>
      <div style={{ fontSize: 12, marginTop: 8, color: trendColor }}>{trend}</div>
      <div style={{ height: 4, width: 56, borderRadius: 999, background: 'var(--crown-accent)', marginTop: 10 }} />
    </CrownCard>
  );
}
