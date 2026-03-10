import CrownCard from '../crown/CrownCard.jsx';

const DEFAULT_EVENTS = [
  { time: '9:00 AM', title: 'Chapel Service' },
  { time: '11:30 AM', title: 'Admissions Tour' },
  { time: '2:30 PM', title: 'Leadership Meeting' },
  { time: '6:00 PM', title: 'Basketball Game' },
];

export default function CalendarCard({
  title = 'Upcoming Events',
  dateLabel = 'March 9',
  events = DEFAULT_EVENTS,
  actionLabel = 'Open',
}) {
  return (
    <CrownCard
      title={title}
      right={<span style={{ fontSize: 12, color: 'var(--crown-muted)' }}>{dateLabel}</span>}
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
            <button className="crown-link" style={{ fontSize: 11 }}>{actionLabel}</button>
          </div>
        ))}
      </div>
    </CrownCard>
  );
}
