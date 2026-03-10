import CrownCard from '../../crown/CrownCard.jsx';

export default function StudentShortcutsCard() {
  const rows = ['Open Assignments', 'View Grades', 'Open Schedule', 'Check Messages'];

  return (
    <CrownCard title="Shortcuts">
      <div style={{ display: 'grid', gap: 10 }}>
        {rows.map((row) => (
          <button
            key={row}
            className="crown-link"
            style={{
              width: '100%',
              textAlign: 'left',
              border: '1px solid var(--crown-border)',
              borderRadius: 10,
              padding: '10px 12px',
              fontSize: 13,
              color: 'var(--crown-brand)',
            }}
          >
            {row}
          </button>
        ))}
      </div>
    </CrownCard>
  );
}
