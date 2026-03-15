import OperationalSnapshotCard from '../OperationalSnapshotCard.jsx';

export default function AttendanceSnapshotCard() {
  const rows = [
    { area: 'Grade 9', rate: '92%', status: 'Watch', next: 'Review absences' },
    { area: 'Grade 7', rate: '95%', status: 'Healthy', next: 'Open details' },
    { area: 'Morning Tardies', rate: '11', status: 'Watch', next: 'Review pattern' },
    { area: 'Unsubmitted Classes', rate: '2', status: 'Needs Action', next: 'Contact teacher' },
  ];

  const columns = [
    { key: 'area', label: 'Area' },
    { key: 'rate', label: 'Rate / Count' },
    { key: 'status', label: 'Status' },
    { key: 'next', label: 'Next View', isLink: true },
  ];

  return (
    <OperationalSnapshotCard
      title="Attendance Snapshot"
      columns={columns}
      rows={rows}
      actionLabel="Open Attendance Detail"
    />
  );
}
