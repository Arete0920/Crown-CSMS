import PrioritiesPanel from '../PrioritiesPanel.jsx';

export default function TeacherPrioritiesPanel() {
  const priorities = [
    'Submit attendance for 1 remaining class',
    'Grade 23 assignments',
    'Respond to 3 parent messages',
    "Prepare tomorrow's lesson notes",
  ];

  return <PrioritiesPanel items={priorities} rightLabel="4 Open" showButton={false} />;
}
