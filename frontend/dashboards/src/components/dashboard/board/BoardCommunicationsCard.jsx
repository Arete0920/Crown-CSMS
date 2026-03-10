import CommunicationsCard from '../CommunicationsCard.jsx';

export default function BoardCommunicationsCard() {
  const items = [
    { title: 'Board packet notice', detail: 'Updated packet posted this morning' },
    { title: 'Chair communication', detail: 'Agenda revisions shared with members' },
    { title: 'Leadership summary', detail: 'Weekly summary available for review' },
  ];

  return (
    <CommunicationsCard
      title="Board Communications"
      rightLabel="Open Center"
      messages={items}
    />
  );
}
