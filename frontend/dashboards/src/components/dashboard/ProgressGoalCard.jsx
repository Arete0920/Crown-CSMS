import CrownCard from '../crown/CrownCard.jsx';

export default function ProgressGoalCard({
  title,
  current,
  goal,
  percentLabel,
  detail,
  colorClass = 'var(--crown-brand)',
}) {
  const percent = Math.min(100, Math.round((current / goal) * 100));

  return (
    <CrownCard title={title} right={<span className="crown-pill">{percentLabel}</span>}>
      <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--crown-ink)' }}>{current.toLocaleString()}</div>
      <div style={{ marginTop: 4, fontSize: 12, color: 'var(--crown-muted)' }}>
        Goal: {goal.toLocaleString()}
      </div>

      <div style={{ marginTop: 12, height: 14, borderRadius: 999, background: 'var(--crown-surface-2)', overflow: 'hidden' }}>
        <div style={{ width: `${percent}%`, height: '100%', background: colorClass }} />
      </div>

      <div style={{ marginTop: 10, fontSize: 12, color: 'var(--crown-muted)' }}>{detail}</div>
    </CrownCard>
  );
}
