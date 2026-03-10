import PrioritiesPanel from '../PrioritiesPanel.jsx';

export default function AttendancePrioritiesPanel() {
  const priorities = [
    'Follow up on 2 missing class attendance entries',
    'Review repeated absences for Grade 9',
    'Confirm tardy intervention list',
    'Prepare weekly attendance summary',
  ];

  return (
    <PrioritiesPanel
      title="Attendance Priorities"
      items={priorities}
      rightLabel="4 Open"
      showButton={false}
    />
  );
}
