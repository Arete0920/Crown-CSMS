import OperationalSnapshotCard from '../OperationalSnapshotCard.jsx';

export default function TeacherClassSnapshotCard() {
  const rows = [
    { className: 'Grade 7 Bible', attendance: '24/25', status: 'Healthy', next: 'Open class' },
    { className: 'Grade 9 English', attendance: '19/22', status: 'Watch', next: 'Review absences' },
    { className: 'Grade 11 History', attendance: '17/18', status: 'Healthy', next: 'Open class' },
  ];

  const columns = [
    { key: 'className', label: 'Class' },
    { key: 'attendance', label: 'Attendance' },
    { key: 'status', label: 'Status' },
    { key: 'next', label: 'Next View', isLink: true },
  ];

  return (
    <OperationalSnapshotCard
      title="Class Snapshot"
      columns={columns}
      rows={rows}
      actionLabel="Open Class Detail"
    />
  );
}
