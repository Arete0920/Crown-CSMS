import CrownCard from '../../crown/CrownCard.jsx';

export default function MasterControlAtAGlanceCard() {
  const items = [
    ['Active Schools', '18'],
    ['Open Tickets', '14'],
    ['Implementations', '3'],
    ['Revenue Processed', '$12.4M'],
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
