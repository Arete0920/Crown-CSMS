import CommunicationsCard from '../CommunicationsCard.jsx';

export default function AttendanceCommunicationsCard() {
  const rows = [
    { title: 'Parent absence notices', detail: '4 new absence notes received' },
    { title: 'Teacher follow-up', detail: '2 attendance reminders sent' },
    { title: 'Intervention communication', detail: '3 attendance concern notices prepared' },
  ];

  return (
    <CommunicationsCard
      title="Attendance Communications"
      rightLabel="Open Center"
      messages={rows}
    />
  );
}
