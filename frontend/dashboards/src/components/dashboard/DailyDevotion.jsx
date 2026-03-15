import CrownCard from '../crown/CrownCard.jsx';

export default function DailyDevotion() {
  return (
    <CrownCard title="Daily Devotion">
      <p style={{ margin: 0, color: 'var(--crown-ink)', fontStyle: 'italic', lineHeight: 1.6 }}>
        "Trust in the Lord with all your heart and lean not on your own understanding."
      </p>
      <p style={{ margin: '6px 0 0 0', color: 'var(--crown-muted)', fontSize: 12 }}>Proverbs 3:5</p>
      <p style={{ marginTop: 12, color: 'var(--crown-muted)', fontSize: 13, lineHeight: 1.6 }}>
        Leadership in Christian education begins with humility before God. Every decision
        shapes the lives of students entrusted to us.
      </p>
      <button className="crown-btn" style={{ marginTop: 12, fontSize: 12 }}>
        Read More
      </button>
    </CrownCard>
  );
}
