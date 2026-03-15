import CrownCard from '../../crown/CrownCard.jsx';

export default function TeacherAtAGlanceCard() {
  const items = [
    ['Students Present', '96'],
    ['Classes Today', '5'],
    ['Messages', '3'],
    ['Assignments Due', '18'],
  ];

  return (
    <CrownCard title="At a Glance">
      <div style={{ display: 'grid', gap: 10 }}>
        {items.map(([label, value]) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
            <span style={{ color: 'var(--crown-muted)' }}>{label}</span>
            <span style={{ color: 'var(--crown-ink)', fontWeight: 700 }}>{value}</span>
          </div>
        ))}
      </div>
    </CrownCard>
  );
}
