import CrownCard from '../../crown/CrownCard.jsx';

export default function AdmissionsApplicantsSnapshotCard() {
  const rows = [
    {
      name: 'Emily Carter',
      grade: '6',
      status: 'Interview Complete',
      nextStep: 'Final Review',
    },
    {
      name: 'Noah Johnson',
      grade: '9',
      status: 'Missing Transcript',
      nextStep: 'Request document',
    },
    {
      name: 'Ava Martinez',
      grade: '11',
      status: 'Application Complete',
      nextStep: 'Schedule interview',
    },
    {
      name: 'Luke Reynolds',
      grade: '4',
      status: 'Accepted',
      nextStep: 'Await response',
    },
    {
      name: 'Sarah Williams',
      grade: '8',
      status: 'Tour Scheduled',
      nextStep: 'Confirm attendance',
    },
  ];

  return (
    <CrownCard
      title="Applicant Snapshot"
      right={
        <button className="crown-link" style={{ fontSize: 12 }}>
          Open Applicant Queue
        </button>
      }
    >
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ textAlign: 'left', color: 'var(--crown-muted)', borderBottom: '1px solid var(--crown-border)' }}>
              <th style={{ padding: '8px 10px 8px 0' }}>Applicant</th>
              <th style={{ padding: '8px 10px 8px 0' }}>Grade</th>
              <th style={{ padding: '8px 10px 8px 0' }}>Status</th>
              <th style={{ padding: '8px 0' }}>Next Step</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.name} style={{ borderBottom: '1px solid var(--crown-border)' }}>
                <td style={{ padding: '9px 10px 9px 0', color: 'var(--crown-ink)' }}>{row.name}</td>
                <td style={{ padding: '9px 10px 9px 0', color: 'var(--crown-muted)' }}>{row.grade}</td>
                <td style={{ padding: '9px 10px 9px 0', color: 'var(--crown-muted)' }}>{row.status}</td>
                <td style={{ padding: '9px 0' }}>
                  <button className="crown-link" style={{ fontSize: 12 }}>{row.nextStep}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </CrownCard>
  );
}
