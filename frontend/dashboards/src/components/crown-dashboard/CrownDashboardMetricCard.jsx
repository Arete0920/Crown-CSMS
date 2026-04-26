import CrownCard from '../launch/CrownCard.jsx';

export default function CrownDashboardMetricCard({ label, value, detail, accent = 'blue' }) {
  return (
    <CrownCard className={`launch-metric-card launch-accent-${accent}`}>
      <div className="launch-metric-label">{label}</div>
      <div className="launch-metric-value">{value}</div>
      <div className="launch-metric-detail">{detail}</div>
    </CrownCard>
  );
}
