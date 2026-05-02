import CrownCard from '../launch/CrownCard.jsx';

export default function CrownFaithCommunityStrip({ faithCommunity = {} }) {
  const devotion = faithCommunity.devotion || {};
  const prayers = Array.isArray(faithCommunity.prayerRequests) ? faithCommunity.prayerRequests : [];
  const announcements = Array.isArray(faithCommunity.announcements) ? faithCommunity.announcements : [];
  const celebrations = Array.isArray(faithCommunity.celebrations) ? faithCommunity.celebrations : [];

  return (
    <section className="launch-dashboard-grid launch-faith-community-strip" aria-label="Faith and Community">
      {/* Daily Devotion */}
      <CrownCard className="launch-faith-card launch-faith-card--devotion">
        <div className="launch-section-kicker">Daily devotion</div>
        <h3 className="launch-faith-title">Morning Word</h3>
        {devotion.scripture && (
          <blockquote className="launch-faith-scripture">
            {devotion.scripture}
          </blockquote>
        )}
        {devotion.reference && (
          <p className="launch-faith-reference">{devotion.reference}</p>
        )}
        {devotion.reflection && (
          <p className="launch-faith-reflection">{devotion.reflection}</p>
        )}
        {devotion.actionLabel && (
          <button type="button" className="launch-button launch-button-ghost launch-faith-action">
            {devotion.actionLabel}
          </button>
        )}
      </CrownCard>

      {/* Prayer Requests */}
      <CrownCard className="launch-faith-card launch-faith-card--prayer">
        <div className="launch-section-kicker">Community prayer</div>
        <h3 className="launch-faith-title">Prayer Requests</h3>
        {prayers.length > 0 ? (
          <ul className="launch-faith-list">
            {prayers.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="launch-faith-empty">No prayer requests today.</p>
        )}
        <button type="button" className="launch-button launch-button-ghost launch-faith-action">
          Submit a Request
        </button>
      </CrownCard>

      {/* Announcements */}
      <CrownCard className="launch-faith-card launch-faith-card--announcements">
        <div className="launch-section-kicker">School announcements</div>
        <h3 className="launch-faith-title">Announcements</h3>
        {announcements.length > 0 ? (
          <ul className="launch-faith-list">
            {announcements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="launch-faith-empty">No announcements today.</p>
        )}
        <button type="button" className="launch-button launch-button-ghost launch-faith-action">
          View All
        </button>
      </CrownCard>

      {/* Celebrations */}
      <CrownCard className="launch-faith-card launch-faith-card--celebrations">
        <div className="launch-section-kicker">Community life</div>
        <h3 className="launch-faith-title">Celebrations</h3>
        {celebrations.length > 0 ? (
          <ul className="launch-faith-celebration-list">
            {celebrations.map((item, idx) => (
              <li key={item.name ?? idx} className={`launch-faith-celebration-item ${item.tone === 'gold' ? 'is-gold' : 'is-good'}`}>
                <strong>{item.name}</strong>
                <span>{item.reason}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="launch-faith-empty">No celebrations today.</p>
        )}
        <button type="button" className="launch-button launch-button-ghost launch-faith-action">
          Add Recognition
        </button>
      </CrownCard>
    </section>
  );
}
