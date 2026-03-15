import CrownCard from '../crown/CrownCard.jsx';

const DEFAULT_COLUMNS = [
  { key: 'name', label: 'Name' },
  { key: 'grade', label: 'Grade' },
  { key: 'status', label: 'Status' },
  { key: 'nextStep', label: 'Next Step', isLink: true },
];

const DEFAULT_ROWS = [
  {
    name: 'Emily Carter',
    grade: '6',
    status: 'Application Complete',
    nextStep: 'Review file',
  },
  {
    name: 'Noah Johnson',
    grade: '9',
    status: 'Tuition Balance Due',
    nextStep: 'Contact family',
  },
  {
    name: 'Ava Martinez',
    grade: '11',
    status: 'Attendance Flag',
    nextStep: 'See details',
  },
  {
    name: 'Luke Reynolds',
    grade: '4',
    status: 'Enrollment Confirmed',
    nextStep: 'Open record',
  },
  {
    name: 'Sarah Williams',
    grade: '8',
    status: 'Aid Review Pending',
    nextStep: 'Review application',
  },
];

function cellAlign(index, total) {
  if (index === total - 1) return 'right';
  return 'left';
}

export default function OperationalSnapshotCard({
  title = 'Operational Snapshot',
  columns = DEFAULT_COLUMNS,
  rows = DEFAULT_ROWS,
  actionLabel = 'Open Dashboard Detail',
}) {
  return (
    <CrownCard
      title={title}
      right={
        <button className="crown-link" style={{ fontSize: 12 }}>
          {actionLabel}
        </button>
      }
    >
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ textAlign: 'left', color: 'var(--crown-muted)', borderBottom: '1px solid var(--crown-border)' }}>
              {columns.map((col, index) => (
                <th
                  key={col.key}
                  style={{
                    padding: index === columns.length - 1 ? '8px 0' : '8px 10px 8px 0',
                    textAlign: cellAlign(index, columns.length),
                  }}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={String(row[columns[0].key])} style={{ borderBottom: '1px solid var(--crown-border)' }}>
                {columns.map((col, index) => (
                  <td
                    key={`${String(row[columns[0].key])}-${col.key}`}
                    style={{
                      padding: index === columns.length - 1 ? '9px 0' : '9px 10px 9px 0',
                      textAlign: cellAlign(index, columns.length),
                      color: index === 0 ? 'var(--crown-ink)' : 'var(--crown-muted)',
                    }}
                  >
                    {col.isLink ? (
                      <button className="crown-link" style={{ fontSize: 12 }}>{row[col.key]}</button>
                    ) : (
                      row[col.key]
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </CrownCard>
  );
}
