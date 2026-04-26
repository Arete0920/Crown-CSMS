import CrownCard from '../launch/CrownCard.jsx';

export default function CrownDashboardActivityFeed({ title = 'Recent Activities', items = [] }) {
  return (
    <CrownCard>
      <div className="launch-section-kicker">Recent Activities</div>
      <h3>{title}</h3>
      <ul className="launch-activity-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </CrownCard>
  );
}
