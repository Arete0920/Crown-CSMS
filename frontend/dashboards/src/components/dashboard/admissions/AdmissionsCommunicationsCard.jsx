import CrownCard from '../../crown/CrownCard.jsx';

export default function AdmissionsCommunicationsCard() {
  const messages = [
    {
      title: 'New parent inquiry messages',
      detail: '3 families waiting for response',
    },
    {
      title: 'Open house reminder',
      detail: 'Email campaign scheduled for tomorrow',
    },
    {
      title: 'Application follow-up',
      detail: '5 incomplete applicants need reminders',
    },
  ];

  return (
    <CrownCard
      title="Admissions Communications"
      right={
        <button className="crown-link" style={{ fontSize: 12 }}>
          Open Center
        </button>
      }
    >
      <div style={{ display: 'grid', gap: 10 }}>
        {messages.map((item) => (
          <div
            key={item.title}
            style={{
              border: '1px solid var(--crown-border)',
              background: '#f8fafc',
              borderRadius: 10,
              padding: 10,
            }}
          >
            <div style={{ fontSize: 13, color: 'var(--crown-ink)', fontWeight: 700 }}>{item.title}</div>
            <div style={{ fontSize: 11, color: 'var(--crown-muted)', marginTop: 4 }}>{item.detail}</div>
          </div>
        ))}
      </div>
    </CrownCard>
  );
}
