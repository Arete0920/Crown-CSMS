import CrownCard from '../launch/CrownCard.jsx';
import { Link, useInRouterContext } from 'react-router';

function ActionControl({ href, className, children }) {
  const hasRouterContext = useInRouterContext();
  const isDataSourceLink = typeof href === 'string' && (href.startsWith('/api/') || href.startsWith('http://') || href.startsWith('https://'));

  if (isDataSourceLink) {
    return (
      <a href={href} className={className} target="_blank" rel="noopener noreferrer">{children}</a>
    );
  }

  return hasRouterContext ? (
    <Link to={href} className={className}>{children}</Link>
  ) : (
    <a href={href} className={className}>{children}</a>
  );
}

export default function CrownFaithCommunityStrip({ faithCommunity = {} }) {
  const devotion = faithCommunity.devotion || {};
  const prayers = Array.isArray(faithCommunity.prayerRequests) ? faithCommunity.prayerRequests : [];
  const announcements = Array.isArray(faithCommunity.announcements) ? faithCommunity.announcements : [];
  const celebrations = Array.isArray(faithCommunity.celebrations) ? faithCommunity.celebrations : [];
  const devotionHref = devotion.actionHref || 'https://www.biblegateway.com/passage/?search=Proverbs%203%3A5&version=KJV';
  const prayerHref = faithCommunity.prayerActionHref || '/spiritual-life';
  const announcementsHref = faithCommunity.announcementsActionHref || '/communications';
  const celebrationsHref = faithCommunity.celebrationsActionHref || '/spiritual-life';

  return (
    <section className="launch-dashboard-grid launch-faith-community-strip" aria-label="Faith and Community">
      {/* Daily Devotion */}
      <CrownCard className="launch-faith-card launch-faith-card--devotion">
        <div className="launch-section-kicker">Daily Devotion</div>
        <h2 className="launch-faith-title">Morning Word</h2>
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
          <ActionControl href={devotionHref} className="launch-button launch-button-ghost launch-faith-action">
            {devotion.actionLabel}
          </ActionControl>
        )}
      </CrownCard>

      {/* Prayer Requests */}
      <CrownCard className="launch-faith-card launch-faith-card--prayer">
        <div className="launch-section-kicker">Community prayer</div>
        <h2 className="launch-faith-title">Prayer Requests</h2>
        {prayers.length > 0 ? (
          <ul className="launch-faith-list">
            {prayers.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="launch-faith-empty">No prayer requests today.</p>
        )}
        <ActionControl href={prayerHref} className="launch-button launch-button-ghost launch-faith-action">
          Submit a Request
        </ActionControl>
      </CrownCard>

      {/* Announcements */}
      <CrownCard className="launch-faith-card launch-faith-card--announcements">
        <div className="launch-section-kicker">School announcements</div>
        <h2 className="launch-faith-title">Announcements</h2>
        {announcements.length > 0 ? (
          <ul className="launch-faith-list">
            {announcements.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="launch-faith-empty">No announcements today.</p>
        )}
        <ActionControl href={announcementsHref} className="launch-button launch-button-ghost launch-faith-action">
          View All
        </ActionControl>
      </CrownCard>

      {/* Celebrations */}
      <CrownCard className="launch-faith-card launch-faith-card--celebrations">
        <div className="launch-section-kicker">Community life</div>
        <h2 className="launch-faith-title">Celebrations</h2>
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
        <ActionControl href={celebrationsHref} className="launch-button launch-button-ghost launch-faith-action">
          Add Recognition
        </ActionControl>
      </CrownCard>
    </section>
  );
}
