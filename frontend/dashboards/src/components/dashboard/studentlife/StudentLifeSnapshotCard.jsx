import OperationalSnapshotCard from '../OperationalSnapshotCard.jsx';

export default function StudentLifeSnapshotCard() {
  const rows = [
    { area: 'Chapel', status: 'Healthy', next: 'Open attendance' },
    { area: 'Service Hours', status: 'Watch', next: 'Review lagging students' },
    { area: 'Mentoring', status: 'Needs Follow-Up', next: 'Open care notes' },
    { area: 'Student Care', status: 'Healthy', next: 'Open referrals' },
  ];

  const columns = [
    { key: 'area', label: 'Area' },
    { key: 'status', label: 'Status' },
    { key: 'next', label: 'Next View', isLink: true },
  ];

  return (
    <OperationalSnapshotCard
      title="Student Life Snapshot"
      columns={columns}
      rows={rows}
      actionLabel="Open Care Detail"
    />
  );
}
