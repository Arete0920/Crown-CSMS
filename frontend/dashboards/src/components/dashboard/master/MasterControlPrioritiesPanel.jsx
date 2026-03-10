import PrioritiesPanel from '../PrioritiesPanel.jsx';

export default function MasterControlPrioritiesPanel() {
  const priorities = [
    'Review 3 implementation milestones',
    'Address billing support spike',
    'Prepare executive weekly summary',
    'Review adoption metrics by school',
  ];

  return (
    <PrioritiesPanel
      title="Platform Priorities"
      items={priorities}
      rightLabel="4 Open"
      showButton={false}
    />
  );
}
