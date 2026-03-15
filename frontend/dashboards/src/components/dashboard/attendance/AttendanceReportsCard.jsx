import ReportSnapshotCard from '../ReportSnapshotCard.jsx';

export default function AttendanceReportsCard() {
  const rows = [
    'Daily Attendance Summary',
    'Repeated Absence Report',
    'Tardy Pattern Analysis',
  ];

  return (
    <ReportSnapshotCard
      title="Attendance Reports"
      rightLabel="View Reports"
      reports={rows}
      showHighlight={false}
    />
  );
}
