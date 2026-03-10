import ReportSnapshotCard from '../ReportSnapshotCard.jsx';

export default function StudentLifeReportsCard() {
  const rows = ['Chapel Attendance Report', 'Service Hours Report', 'Care Referral Summary'];

  return (
    <ReportSnapshotCard
      title="Chaplain Reports"
      rightLabel="View Reports"
      reports={rows}
      showHighlight={false}
    />
  );
}
