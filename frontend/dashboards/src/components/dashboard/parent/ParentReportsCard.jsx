import ReportSnapshotCard from '../ReportSnapshotCard.jsx';

export default function ParentReportsCard() {
  const rows = ['Current Grades', 'Attendance Summary', 'Tuition Statement'];

  return (
    <ReportSnapshotCard
      title="Family Reports"
      rightLabel="View Reports"
      reports={rows}
      showHighlight={false}
    />
  );
}
