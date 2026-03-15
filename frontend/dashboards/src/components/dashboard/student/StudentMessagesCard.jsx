import CommunicationsCard from '../CommunicationsCard.jsx';

export default function StudentMessagesCard() {
  const rows = [
    { title: 'Teacher Message', detail: 'Reminder to bring project notes tomorrow' },
    { title: 'School Announcement', detail: 'Chapel schedule updated for Friday' },
    { title: 'Club Notice', detail: 'Service club meeting after school' },
  ];

  return (
    <CommunicationsCard
      title="Messages"
      rightLabel="Open Inbox"
      messages={rows}
    />
  );
}
