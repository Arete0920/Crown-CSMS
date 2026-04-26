import CrownCard from '../launch/CrownCard.jsx';

export default function CrownDashboardMetricCard({ label, value, detail, accent = 'blue' }) {
  const badge = String(label || '').trim().slice(0, 1).toUpperCase();

  return (
    <CrownCard className={`launch-metric-card launch-accent-${accent}`}>
      <div className="launch-metric-toprow">
        <div className="launch-metric-label">{label}</div>
        <div className="launch-metric-icon-bubble" aria-hidden="true">{badge || 'C'}</div>
      </div>
      <div className="launch-metric-value">{value}</div>
      <div className="launch-metric-detail">{detail}</div>
    </CrownCard>
  );
}
