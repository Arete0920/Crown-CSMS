import CrownCard from '../crown/CrownCard.jsx';

const PRIORITIES = [
  'Review 3 admissions applications',
  'Approve 5 financial aid recommendations',
  'Follow up on 2 attendance concerns',
  'Prepare weekly leadership summary',
  'Respond to parent communication backlog',
];

export default function PrioritiesPanel({
  title = "Today's Priorities",
  items = PRIORITIES,
  rightLabel = '5 Open',
  buttonLabel = 'View Full Task List',
  showButton = true,
}) {
  return (
    <CrownCard
      title={title}
      right={rightLabel ? <span className="crown-pill">{rightLabel}</span> : null}
    >
      <ul style={{ margin: 0, paddingLeft: 16, color: 'var(--crown-muted)', fontSize: 13, lineHeight: 1.8 }}>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {showButton ? (
        <button className="crown-btn" style={{ marginTop: 12, fontSize: 12 }}>
          {buttonLabel}
        </button>
      ) : null}
    </CrownCard>
  );
}
