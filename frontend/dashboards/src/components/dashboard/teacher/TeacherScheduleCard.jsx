import CalendarCard from '../CalendarCard.jsx';

export default function TeacherScheduleCard() {
  const rows = [
    { time: '8:00 AM', title: 'Grade 7 Bible' },
    { time: '9:15 AM', title: 'Grade 9 English' },
    { time: '11:00 AM', title: 'Grade 11 History' },
    { time: '1:15 PM', title: 'Prep Period' },
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
