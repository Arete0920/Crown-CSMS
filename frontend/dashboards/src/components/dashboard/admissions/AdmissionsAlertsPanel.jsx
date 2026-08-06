import CrownCard from '../../crown/CrownCard.jsx';

function toneStyles(tone) {
  if (tone === 'red') {
    return {
      background: 'var(--crown-danger-bg)',
      border: '1px solid var(--crown-danger)',
      color: 'var(--crown-danger)',
    };
  }
  return {
    background: 'var(--crown-warn-bg)',
    border: '1px solid var(--crown-warn)',
    color: 'var(--crown-warn)',
  };
}

export default function AdmissionsAlertsPanel() {
  const alerts = [
    {
      label: 'Incomplete Files',
      detail: '8 applications missing documents',
      tone: 'amber',
    },
    {
      label: 'Follow-Up Delay',
      detail: '5 inquiries have not been contacted in 48 hours',
      tone: 'red',
    },
    {
      label: 'Interview Queue',
      detail: '4 applicant interviews not yet scheduled',
      tone: 'amber',
    },
    {
      label: 'Decision Pending',
      detail: '3 applications are ready for final review',
      tone: 'red',
    },
  ];

  return (
    <CrownCard title="Admissions Alerts" right={<span className="crown-pill">4 Active</span>}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {alerts.map((alert) => {
          const style = toneStyles(alert.tone);
          return (
            <div key={alert.label} style={{ ...style, borderRadius: 8, padding: '8px 10px' }}>
              <div style={{ fontSize: 12, fontWeight: 700 }}>{alert.label}</div>
              <div style={{ fontSize: 12, marginTop: 2 }}>{alert.detail}</div>
            </div>
          );
        })}
      </div>
      <button className="crown-btn" style={{ marginTop: 12, fontSize: 12 }}>
        View All Admissions Alerts
      </button>
    </CrownCard>
  );
}
