import OperationalSnapshotCard from '../OperationalSnapshotCard.jsx';

export default function BoardStrategicSnapshotCard() {
  const rows = [
    { area: 'Enrollment', status: 'Healthy', nextStep: 'Review trend' },
    { area: 'Finance', status: 'Stable', nextStep: 'Open packet' },
    { area: 'Retention', status: 'Watch', nextStep: 'Review grade data' },
    { area: 'Mission Engagement', status: 'Healthy', nextStep: 'Open summary' },
    { area: 'Academic Performance', status: 'Stable', nextStep: 'View report' },
  ];

  const columns = [
    { key: 'area', label: 'Area' },
    { key: 'status', label: 'Status' },
    { key: 'nextStep', label: 'Next View', isLink: true },
  ];

  return (
    <OperationalSnapshotCard
      title="Strategic Snapshot"
      columns={columns}
      rows={rows}
      actionLabel="Open Governance Detail"
    />
  );
}
