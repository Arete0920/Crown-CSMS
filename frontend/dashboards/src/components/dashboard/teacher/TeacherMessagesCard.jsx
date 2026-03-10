import CommunicationsCard from '../CommunicationsCard.jsx';

export default function TeacherMessagesCard() {
  const rows = [
    { title: 'Parent message - Carter family', detail: 'Question about missing assignment' },
    { title: 'Admin note', detail: 'Reminder: attendance due by 10 AM' },
    { title: 'Student message', detail: 'Request for makeup work' },
  ];

  return (
    <CommunicationsCard
      title="Messages"
      rightLabel="Open Inbox"
      messages={rows}
    />
  );
}
