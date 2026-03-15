import CrownCard from '../crown/CrownCard.jsx';

export default function PrayerRequests() {
  return (
    <CrownCard title="Prayer Requests">
      <ul style={{ margin: 0, paddingLeft: 16, color: 'var(--crown-muted)', fontSize: 13, lineHeight: 1.8 }}>
        <li>Mrs Carter surgery recovery</li>
        <li>Wisdom for leadership meetings</li>
        <li>Mission trip safety</li>
      </ul>
      <button className="crown-btn" style={{ marginTop: 12, fontSize: 12 }}>
        Submit Prayer Request
      </button>
    </CrownCard>
  );
}
