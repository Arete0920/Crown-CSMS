import CrownCard from '../crown/CrownCard.jsx';

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

export default function AlertsPanel({
  alerts = [],
  title = 'Alerts',
  rightLabel,
  buttonLabel = 'View All Alerts',
  showButton = true,
}) {
  const data = alerts.length
    ? alerts
    : [
        { label: 'Attendance Warning', detail: '12 students absent today', tone: 'amber' },
        { label: 'Finance Alert', detail: '7 overdue tuition accounts', tone: 'red' },
        { label: 'Admissions Alert', detail: '2 incomplete application files', tone: 'amber' },
        { label: 'Discipline Follow-Up', detail: '1 case requires administrator review', tone: 'red' },
      ];

  const activeCountLabel = rightLabel || `${data.length} Active`;

  return (
    <CrownCard
      title={title}
      right={<span className="crown-pill">{activeCountLabel}</span>}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {data.map((alert) => {
          const style = toneStyles(alert.tone);
          return (
            <div key={alert.label} style={{ ...style, borderRadius: 8, padding: '8px 10px' }}>
              <div style={{ fontSize: 12, fontWeight: 700 }}>{alert.label}</div>
              <div style={{ fontSize: 12, marginTop: 2 }}>{alert.detail}</div>
            </div>
          );
        })}
      </div>
      {showButton ? (
        <button className="crown-btn" style={{ marginTop: 12, fontSize: 12 }}>
          {buttonLabel}
        </button>
      ) : null}
    </CrownCard>
  );
}
