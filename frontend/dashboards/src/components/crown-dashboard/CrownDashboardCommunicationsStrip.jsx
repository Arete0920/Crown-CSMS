import CrownCard from '../launch/CrownCard.jsx';
import { Link, useInRouterContext } from 'react-router-dom';

function ActionControl({ href, className, children }) {
  const hasRouterContext = useInRouterContext();

  return hasRouterContext ? (
    <Link to={href} className={className}>{children}</Link>
  ) : (
    <a href={href} className={className}>{children}</a>
  );
}

export default function CrownDashboardCommunicationsStrip({ communications = {} }) {
  const inboxItems = Array.isArray(communications.inboxItems) ? communications.inboxItems : [];
  const announcementItems = Array.isArray(communications.announcementItems) ? communications.announcementItems : [];
  const urgentItems = Array.isArray(communications.urgentItems) ? communications.urgentItems : [];

  return (
    <section className="launch-dashboard-grid launch-communications-strip" aria-label="Communications">
      <CrownCard className="launch-communications-card launch-communications-card--inbox">
        <div className="launch-section-kicker">Communications inbox</div>
        <h3 className="launch-communications-title">{communications.inboxTitle || 'Unread and waiting'}</h3>
        <p className="launch-communications-summary">{communications.inboxSummary || 'No inbox summary available.'}</p>
        {inboxItems.length > 0 ? (
          <ul className="launch-communications-list">
            {inboxItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="launch-communications-empty">No pending inbox items.</p>
        )}
        <ActionControl href={communications.inboxActionHref || '/communications'} className="launch-button launch-button-secondary launch-communications-action">
          {communications.inboxActionLabel || 'Open Inbox'}
        </ActionControl>
      </CrownCard>

      <CrownCard className="launch-communications-card launch-communications-card--announcements">
        <div className="launch-section-kicker">School notices</div>
        <h3 className="launch-communications-title">{communications.announcementsTitle || 'Announcements and bulletin'}</h3>
        <p className="launch-communications-summary">{communications.announcementsSummary || 'No announcement summary available.'}</p>
        {announcementItems.length > 0 ? (
          <ul className="launch-communications-list">
            {announcementItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="launch-communications-empty">No announcements available.</p>
        )}
        <ActionControl href={communications.announcementsActionHref || '/communications'} className="launch-button launch-button-secondary launch-communications-action">
          {communications.announcementsActionLabel || 'View Announcements'}
        </ActionControl>
      </CrownCard>

      <CrownCard className="launch-communications-card launch-communications-card--alerts">
        <div className="launch-section-kicker">Urgent communication risk</div>
        <h3 className="launch-communications-title">{communications.urgentTitle || 'Alerts and escalations'}</h3>
        <p className="launch-communications-summary">{communications.urgentSummary || 'No urgent communication summary available.'}</p>
        {urgentItems.length > 0 ? (
          <ul className="launch-communications-list">
            {urgentItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="launch-communications-empty">No urgent alerts at this time.</p>
        )}
        <ActionControl href={communications.urgentActionHref || '/communications'} className="launch-button launch-button-secondary launch-communications-action">
          {communications.urgentActionLabel || 'Review Alerts'}
        </ActionControl>
      </CrownCard>
    </section>
  );
}
