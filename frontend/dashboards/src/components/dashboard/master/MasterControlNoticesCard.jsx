import CrownCard from '../../crown/CrownCard.jsx';

export default function MasterControlNoticesCard() {
  const rows = [
    'One implementation kickoff this week',
    'Support queue elevated on billing questions',
    'New product walkthrough ready for schools',
  ];

  return (
    <CrownCard title="Platform Notices">
      <ul style={{ margin: 0, paddingLeft: 16, color: 'var(--crown-muted)', fontSize: 13, lineHeight: 1.8 }}>
        {rows.map((row) => (
          <li key={row}>{row}</li>
        ))}
      </ul>
    </CrownCard>
  );
}
