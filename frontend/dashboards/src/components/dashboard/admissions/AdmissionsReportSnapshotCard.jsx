import CrownCard from '../../crown/CrownCard.jsx';

export default function AdmissionsReportSnapshotCard() {
  const reports = [
    'Admissions Funnel Summary',
    'Applications by Source',
    'Incomplete File Report',
  ];

  return (
    <CrownCard
      title="Admissions Reports"
      right={
        <button className="crown-link" style={{ fontSize: 12 }}>
          View Reports
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

      <div
        style={{
          marginTop: 12,
          borderRadius: 10,
          border: '1px solid #fcd34d',
          background: '#fffbeb',
          padding: 10,
        }}
      >
        <div style={{ fontSize: 13, fontWeight: 800, color: '#92400e' }}>Weekly Enrollment Brief</div>
        <div style={{ fontSize: 11, color: '#b45309', marginTop: 4 }}>
          Ready for leadership review and admissions meeting prep.
        </div>
      </div>
    </CrownCard>
  );
}
