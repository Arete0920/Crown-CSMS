import ReportSnapshotCard from '../ReportSnapshotCard.jsx';

export default function BoardReportSnapshotCard() {
  const reports = [
    'Board Packet',
    'Strategic Enrollment Summary',
    'Monthly Finance Packet',
  ];

  return (
    <ReportSnapshotCard
      title="Board Reports"
      rightLabel="View Reports"
      reports={reports}
      showHighlight={false}
    />
  );
}
