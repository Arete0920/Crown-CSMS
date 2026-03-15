import CrownCard from '../crown/CrownCard.jsx';

const DEFAULT_ITEMS = [
  {
    title: 'New student enrolled - Emily Carter',
    meta: '10 minutes ago',
  },
  {
    title: 'Payment received - Johnson family',
    meta: '24 minutes ago',
  },
  {
    title: 'Admissions interview completed - Luke Reynolds',
    meta: '42 minutes ago',
  },
  {
    title: 'Attendance alert generated for Grade 9',
    meta: '1 hour ago',
  },
  {
    title: 'Faculty announcement posted',
    meta: '2 hours ago',
  },
];

export default function ActivityFeedCard({
  title = 'Recent Activity',
  items = DEFAULT_ITEMS,
  actionLabel = 'View All',
}) {
  return (
    <CrownCard
      title={title}
      right={
        <button className="crown-link" style={{ fontSize: 12 }}>
          {actionLabel}
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
