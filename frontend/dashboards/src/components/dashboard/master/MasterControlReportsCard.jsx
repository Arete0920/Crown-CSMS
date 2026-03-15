import ReportSnapshotCard from '../ReportSnapshotCard.jsx';

export default function MasterControlReportsCard() {
  const rows = ['Executive Summary', 'School Adoption Report', 'Revenue Processing Summary'];

  return (
    <ReportSnapshotCard
      title="Executive Reports"
      rightLabel="View Reports"
      reports={rows}
      showHighlight={false}
    />
  );
}
