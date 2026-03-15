import CrownCard from '../../crown/CrownCard.jsx';

const PRIORITIES = [
  'Follow up with 8 incomplete applications',
  'Confirm 4 family tours for this week',
  'Review 6 interview notes',
  'Send acceptance packets to 3 families',
  'Respond to parent inquiry backlog',
];

export default function AdmissionsPrioritiesPanel() {
  return (
    <CrownCard
      title="Admissions Priorities"
      right={<span className="crown-pill">5 Open</span>}
    >
      <ul style={{ margin: 0, paddingLeft: 16, color: 'var(--crown-muted)', fontSize: 13, lineHeight: 1.8 }}>
        {PRIORITIES.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <button className="crown-btn" style={{ marginTop: 12, fontSize: 12 }}>
        Open Task Queue
      </button>
    </CrownCard>
  );
}
