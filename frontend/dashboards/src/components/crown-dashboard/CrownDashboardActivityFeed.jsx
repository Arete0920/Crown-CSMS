import CrownCard from '../launch/CrownCard.jsx';

export default function CrownDashboardActivityFeed({
  title = 'Recent Activities',
  items = [],
  kicker = 'Operational Activity',
}) {
  const rows = items.map((item, idx) => ({
    id: `${idx}-${item}`,
    message: item,
    time: idx === 0 ? 'Now' : `${idx + 1}h ago`,
    state: idx <= 1 ? 'Completed' : 'Queued',
  }));

  return (
    <CrownCard>
      <div className="launch-section-kicker">{kicker}</div>
      <h3>{title}</h3>
      <ul className="launch-activity-list">
        {rows.map((row) => (
          <li key={row.id} className="launch-activity-item">
            <span className="launch-activity-dot" aria-hidden="true" />
            <span className="launch-activity-message">{row.message}</span>
            <span className="launch-activity-time">{row.time}</span>
            <span className={`launch-activity-state ${row.state === 'Completed' ? 'is-good' : ''}`}>{row.state}</span>
          </li>
        ))}
      </ul>
    </CrownCard>
  );
}
