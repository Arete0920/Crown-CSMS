import CalendarCard from '../CalendarCard.jsx';

export default function MasterControlCalendarCard() {
  const rows = [
    { time: 'Wed 10:00 AM', title: 'Implementation Kickoff' },
    { time: 'Thu 2:00 PM', title: 'Executive Product Review' },
    { time: 'Fri 1:00 PM', title: 'Support Queue Review' },
  ];

  return (
    <CalendarCard
      title="Upcoming Implementations"
      dateLabel="This Week"
      events={rows}
      actionLabel="Open"
    />
  );
}
