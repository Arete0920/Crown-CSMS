import OperationalSnapshotCard from '../OperationalSnapshotCard.jsx';

export default function ParentChildrenSnapshotCard() {
  const rows = [
    { child: 'Emily Carter', grade: '6', status: 'Healthy', next: 'Open student' },
    { child: 'Noah Carter', grade: '9', status: 'Missing Work', next: 'Review assignments' },
    { child: 'Ava Carter', grade: '11', status: 'Healthy', next: 'Open student' },
  ];

  const columns = [
    { key: 'child', label: 'Child' },
    { key: 'grade', label: 'Grade' },
    { key: 'status', label: 'Status' },
    { key: 'next', label: 'Next View', isLink: true },
  ];

  return (
    <OperationalSnapshotCard
      title="Children Snapshot"
      columns={columns}
      rows={rows}
      actionLabel="Open Family Detail"
    />
  );
}
