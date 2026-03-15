import CalendarCard from '../CalendarCard.jsx';

export default function AttendanceCalendarCard() {
  const rows = [
    { time: '8:00 AM', title: 'Attendance submission window opens' },
    { time: '10:00 AM', title: 'Unsubmitted class check' },
    { time: '2:00 PM', title: 'Absence intervention review' },
  ];

  return (
    <CalendarCard
      title="Attendance Timeline"
      dateLabel="Today"
      events={rows}
      actionLabel="Open"
    />
  );
}
