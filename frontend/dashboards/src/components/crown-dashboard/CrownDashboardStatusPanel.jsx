import CrownCard from '../launch/CrownCard.jsx';

export default function CrownDashboardStatusPanel({ title = 'System Status', statuses = [] }) {
  return (
    <CrownCard>
      <div className="launch-section-kicker">System Status</div>
      <h3>{title}</h3>
      <div className="launch-status-list">
        {statuses.map((item) => (
          <div key={item.label} className="launch-status-row">
            <span>{item.label}</span>
            <span className="launch-status-pill">{item.state}</span>
          </div>
        ))}
      </div>
    </CrownCard>
  );
}
