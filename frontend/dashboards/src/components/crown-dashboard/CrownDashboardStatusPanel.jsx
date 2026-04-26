import CrownCard from '../launch/CrownCard.jsx';

export default function CrownDashboardStatusPanel({ title = 'System Status', statuses = [], kicker = 'System Status' }) {
  return (
    <CrownCard>
      <div className="launch-section-kicker">{kicker}</div>
      <h3>{title}</h3>
      <div className="launch-status-list">
        {statuses.map((item) => (
          <div key={item.label} className="launch-status-row">
            <span>{item.label}</span>
            <span
              className={`launch-status-pill ${/healthy|ready|stable|complete|on schedule/i.test(item.state) ? 'is-good' : 'is-warn'}`}
            >
              {item.state}
            </span>
          </div>
        ))}
      </div>
    </CrownCard>
  );
}
