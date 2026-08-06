import CrownCard from '../../crown/CrownCard.jsx';

export default function AdmissionsActivityFeedCard() {
  const items = [
    {
      title: 'New inquiry submitted - Carter family',
      meta: '12 minutes ago',
    },
    {
      title: 'Tour scheduled - Reynolds family',
      meta: '25 minutes ago',
    },
    {
      title: 'Application completed - Ava Martinez',
      meta: '46 minutes ago',
    },
    {
      title: 'Interview notes uploaded - Luke Johnson',
      meta: '1 hour ago',
    },
    {
      title: 'Acceptance email sent - Emily Carter',
      meta: '2 hours ago',
    },
  ];

  return (
    <CrownCard
      title="Recent Admissions Activity"
      right={
        <button className="crown-link" style={{ fontSize: 12 }}>
          View All
        </button>
      }
    >
      <div style={{ display: 'grid', gap: 10 }}>
        {items.map((item) => (
          <div
            key={item.title}
            style={{
              borderBottom: '1px solid var(--crown-border)',
              paddingBottom: 10,
            }}
          >
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--crown-ink)' }}>{item.title}</div>
            <div style={{ fontSize: 11, color: 'var(--crown-muted)', marginTop: 4 }}>{item.meta}</div>
          </div>
        ))}
      </div>
    </CrownCard>
  );
}
