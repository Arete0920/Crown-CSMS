import CrownCard from '../../crown/CrownCard.jsx';

export default function ParentAtAGlanceCard() {
  const items = [
    ['Children Enrolled', '3'],
    ['Assignments Due', '7'],
    ['Messages', '2'],
    ['Next Events', '4'],
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
