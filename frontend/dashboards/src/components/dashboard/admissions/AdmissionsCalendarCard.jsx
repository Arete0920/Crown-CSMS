import CrownCard from '../../crown/CrownCard.jsx';

export default function AdmissionsCalendarCard() {
  const events = [
    { time: '9:30 AM', title: 'Family Tour - Carter family' },
    { time: '11:00 AM', title: 'Admissions Interview - Noah Johnson' },
    { time: '1:30 PM', title: 'Open House Planning Meeting' },
    { time: '6:00 PM', title: 'Prospective Parent Event' },
  ];

  return (
    <CrownCard
      title="Upcoming Tours and Events"
      right={<span style={{ fontSize: 12, color: 'var(--crown-muted)' }}>March 9</span>}
    >
      <div style={{ display: 'grid', gap: 10 }}>
        {events.map((event) => (
          <div
            key={`${event.time}-${event.title}`}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: 10,
              borderBottom: '1px solid var(--crown-border)',
              paddingBottom: 10,
            }}
          >
            <div>
              <div style={{ fontSize: 13, color: 'var(--crown-ink)', fontWeight: 700 }}>{event.title}</div>
              <div style={{ fontSize: 11, color: 'var(--crown-muted)', marginTop: 4 }}>{event.time}</div>
            </div>
            <button className="crown-link" style={{ fontSize: 11 }}>Open</button>
          </div>
        ))}
      </div>
    </CrownCard>
  );
}
