import CrownCard from '../crown/CrownCard.jsx';

const DEFAULT_MESSAGES = [
  {
    title: 'Parent message backlog',
    detail: '3 messages waiting for response',
  },
  {
    title: 'Faculty announcement',
    detail: 'New staff memo posted this morning',
  },
  {
    title: 'School reminder',
    detail: 'Field trip forms due tomorrow',
  },
];

export default function CommunicationsCard({
  title = 'Communications',
  rightLabel = 'Open Center',
  messages = DEFAULT_MESSAGES,
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
