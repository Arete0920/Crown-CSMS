import CommunicationsCard from '../CommunicationsCard.jsx';

export default function StudentLifeCommunicationsCard() {
  const rows = [
    { title: 'Care Team Note', detail: 'Weekly follow-up reminders posted' },
    { title: 'Chapel Communication', detail: 'Speaker and worship outline confirmed' },
    { title: 'Service Reminder', detail: 'Saturday team email scheduled' },
  ];

  return (
    <CommunicationsCard
      title="Care Communications"
      rightLabel="Open Care Center"
      messages={rows}
    />
  );
}
