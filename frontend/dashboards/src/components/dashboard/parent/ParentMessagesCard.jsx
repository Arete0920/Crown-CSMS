import CommunicationsCard from '../CommunicationsCard.jsx';

export default function ParentMessagesCard() {
  const rows = [
    { title: 'Teacher Message', detail: "Question about Noah's assignment completion" },
    { title: 'School Reminder', detail: 'Event permission forms due tomorrow' },
    { title: 'Billing Notice', detail: 'Monthly statement posted' },
  ];

  return (
    <CommunicationsCard
      title="Messages and Announcements"
      rightLabel="Open Center"
      messages={rows}
    />
  );
}
