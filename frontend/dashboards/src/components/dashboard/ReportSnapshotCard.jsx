import CrownCard from '../crown/CrownCard.jsx';

const DEFAULT_REPORTS = [
  'Weekly Enrollment Summary',
  'Monthly Financial Snapshot',
  'Attendance Exceptions Report',
];

export default function ReportSnapshotCard({
  title = 'Report Snapshot',
  rightLabel = 'View Reports',
  reports = DEFAULT_REPORTS,
  showHighlight = true,
  highlightTitle = 'Latest Board Packet',
  highlightDetail = 'Updated this morning and ready for review.',
}) {
  return (
    <CrownCard
      title={title}
      right={
        <button className="crown-link" style={{ fontSize: 12 }}>
          {rightLabel}
        </button>
      }
    >
      <div style={{ display: 'grid', gap: 10 }}>
        {reports.map((report) => (
          <div
            key={report}
            style={{
              border: '1px solid var(--crown-border)',
              borderRadius: 10,
              padding: 10,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontSize: 13, color: 'var(--crown-ink)' }}>{report}</span>
            <button className="crown-link" style={{ fontSize: 11 }}>Open</button>
          </div>
        ))}
      </div>

      {showHighlight ? (
        <div
          style={{
            marginTop: 12,
            borderRadius: 10,
            border: '1px solid #fcd34d',
            background: '#fffbeb',
            padding: 10,
          }}
        >
          <div style={{ fontSize: 13, fontWeight: 800, color: '#92400e' }}>{highlightTitle}</div>
          <div style={{ fontSize: 11, color: '#b45309', marginTop: 4 }}>
            {highlightDetail}
          </div>
        </div>
      ) : null}
    </CrownCard>
  );
}
