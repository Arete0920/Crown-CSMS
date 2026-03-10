import PrioritiesPanel from '../PrioritiesPanel.jsx';

export default function ParentPrioritiesPanel() {
  const priorities = [
    'Review 7 upcoming assignments',
    'Read 2 school messages',
    'Submit one event permission form',
    'Review current tuition balance',
  ];

  return (
    <PrioritiesPanel
      title="Family Priorities"
      items={priorities}
      rightLabel="4 Open"
      showButton={false}
    />
  );
}
