import CalendarCard from '../CalendarCard.jsx';

export default function StudentScheduleCard() {
  const rows = [
    { time: '8:00 AM', title: 'Bible' },
    { time: '9:00 AM', title: 'English' },
    { time: '10:15 AM', title: 'History' },
    { time: '1:00 PM', title: 'Science' },
  ];

  return (
    <CalendarCard
      title="Today's Schedule"
      dateLabel="Today"
      events={rows}
      actionLabel="Open"
    />
  );
}
