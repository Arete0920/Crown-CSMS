import OperationalSnapshotCard from '../OperationalSnapshotCard.jsx';

export default function StudentCourseSnapshotCard() {
  const rows = [
    { course: 'Bible', grade: '92%', status: 'Healthy', next: 'Open course' },
    { course: 'English', grade: '87%', status: 'Healthy', next: 'Open course' },
    { course: 'History', grade: '84%', status: 'Watch', next: 'Review work' },
    { course: 'Science', grade: '91%', status: 'Healthy', next: 'Open course' },
  ];

  const columns = [
    { key: 'course', label: 'Course' },
    { key: 'grade', label: 'Grade' },
    { key: 'status', label: 'Status' },
    { key: 'next', label: 'Next View', isLink: true },
  ];

  return (
    <OperationalSnapshotCard
      title="Course Snapshot"
      columns={columns}
      rows={rows}
      actionLabel="Open Student Detail"
    />
  );
}
