import CalendarCard from '../CalendarCard.jsx';

export default function ParentCalendarCard() {
  const rows = [
    { time: 'Mar 10', title: 'Field Trip - Grade 6' },
    { time: 'Mar 12', title: 'Basketball Game' },
    { time: 'Mar 14', title: 'Parent-Teacher Conferences' },
  ];

  return (
    <CalendarCard
      title="Next Events"
      dateLabel="This Week"
      events={rows}
      actionLabel="Open"
    />
  );
}
