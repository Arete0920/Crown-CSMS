import CalendarCard from '../CalendarCard.jsx';

export default function StudentLifeCalendarCard() {
  const rows = [
    { time: 'Fri 9:00 AM', title: 'Weekly Chapel' },
    { time: 'Sat 8:00 AM', title: 'Service Project' },
    { time: 'Mon 2:30 PM', title: 'Mentor Group Meeting' },
  ];

  return (
    <CalendarCard
      title="Upcoming Chapels and Events"
      dateLabel="This Week"
      events={rows}
      actionLabel="Open"
    />
  );
}
