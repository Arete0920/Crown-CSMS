import PrioritiesPanel from '../PrioritiesPanel.jsx';

export default function StudentPrioritiesPanel() {
  const priorities = [
    'Complete 2 assignments due today',
    'Review quiz corrections',
    'Read new teacher announcement',
    "Prepare for tomorrow's Bible class",
  ];

  return <PrioritiesPanel items={priorities} rightLabel="4 Open" showButton={false} />;
}
