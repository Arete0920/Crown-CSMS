import CalendarCard from '../CalendarCard.jsx';

export default function BoardCalendarCard() {
  const events = [
    { time: 'March 15', title: 'Board Meeting' },
    { time: 'March 20', title: 'Finance Committee Review' },
    { time: 'March 28', title: 'Strategic Planning Session' },
  ];

  return (
    <CalendarCard
      title="Upcoming Meetings and Events"
      dateLabel="This Month"
      events={events}
      actionLabel="Open"
    />
  );
}
