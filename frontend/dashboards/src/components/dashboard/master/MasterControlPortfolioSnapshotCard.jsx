import OperationalSnapshotCard from '../OperationalSnapshotCard.jsx';

export default function MasterControlPortfolioSnapshotCard() {
  const rows = [
    { school: 'Heritage Christian Academy', status: 'Healthy', next: 'Open account' },
    { school: 'Calvary Christian School', status: 'Watch', next: 'Review adoption' },
    { school: 'Grace Academy', status: 'Healthy', next: 'Open account' },
    { school: 'Veritas Christian', status: 'Implementation', next: 'Open onboarding' },
  ];

  const columns = [
    { key: 'school', label: 'School' },
    { key: 'status', label: 'Status' },
    { key: 'next', label: 'Next View', isLink: true },
  ];

  return (
    <OperationalSnapshotCard
      title="School Portfolio Snapshot"
      columns={columns}
      rows={rows}
      actionLabel="Open Portfolio Detail"
    />
  );
}
