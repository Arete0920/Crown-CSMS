import { Link, useInRouterContext } from 'react-router-dom';

/* ── Microsoft 365 product icons (inline SVG, brand-accurate) ─────────── */

function TeamsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect width="20" height="20" rx="5" fill="#6264A7" />
      {/* large person (foreground) */}
      <circle cx="9" cy="7.5" r="3" fill="white" />
      <path d="M3 16.5C3 13.5 5.7 11 9 11s6 2.5 6 5.5v.5H3v-.5z" fill="white" />
      {/* small person (background, right) */}
      <circle cx="15" cy="7" r="2" fill="white" fillOpacity=".7" />
      <path d="M13 12.5h2a2 2 0 0 1 2 2v2h-4v-4z" fill="white" fillOpacity=".5" />
    </svg>
  );
}

function OutlookIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect width="20" height="20" rx="5" fill="#0078D4" />
      {/* envelope body */}
      <rect x="2" y="6" width="11" height="9" rx="1.5" fill="white" fillOpacity=".9" />
      {/* O circle */}
      <circle cx="7.5" cy="10.5" r="2.5" fill="#0078D4" />
      {/* right panel (web tile detail) */}
      <rect x="12" y="7" width="6" height="7" rx="1" fill="white" fillOpacity=".65" />
      {/* envelope fold line */}
      <path d="M2 6.5l5 3.5 5-3.5" stroke="#0078D4" strokeWidth="1" strokeOpacity=".3" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect width="20" height="20" rx="5" fill="#0364B8" />
      {/* calendar body */}
      <rect x="3" y="6" width="14" height="11" rx="1.5" fill="white" fillOpacity=".9" />
      {/* header band */}
      <rect x="3" y="6" width="14" height="4" rx="1.5" fill="white" />
      {/* pin knobs */}
      <rect x="6" y="4" width="2" height="4" rx="1" fill="white" />
      <rect x="12" y="4" width="2" height="4" rx="1" fill="white" />
      {/* day dots */}
      <rect x="5.5" y="12.5" width="2" height="2" rx=".5" fill="#0364B8" fillOpacity=".6" />
      <rect x="9"   y="12.5" width="2" height="2" rx=".5" fill="#0364B8" fillOpacity=".6" />
      <rect x="12.5" y="12.5" width="2" height="2" rx=".5" fill="#0364B8" fillOpacity=".6" />
    </svg>
  );
}

/* ── CrownHeroHeader ──────────────────────────────────────────────────── */

export default function CrownHeroHeader({
  schoolName = 'Heritage Christian Academy',
  updatesCount = 3,
  userInitials = 'SJ',
  userAvatar = null,
  title,
}) {
  const hasRouterContext = useInRouterContext();

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="launch-hero-header" role="banner">
      {/* ── Top utility row ─────────────────────────────────────────── */}
      <div className="launch-hero-topbar">
        <label className="launch-search launch-hero-search" aria-label="Search">
          <span className="launch-search-icon" aria-hidden="true" />
          <input
            type="search"
            placeholder="Search students, workflows, and actions"
            aria-label="Search students, workflows, and actions"
          />
        </label>

        <div className="launch-topbar-actions">
          {hasRouterContext ? (
            <Link to="/communications" className="launch-icon-button launch-hero-action-btn">
              Updates <span className="launch-counter">{updatesCount}</span>
            </Link>
          ) : (
            <a href="/communications" className="launch-icon-button launch-hero-action-btn">
              Updates <span className="launch-counter">{updatesCount}</span>
            </a>
          )}

          {hasRouterContext ? (
            <Link to="/settings" className="launch-icon-button launch-hero-action-btn">Help</Link>
          ) : (
            <a href="/settings" className="launch-icon-button launch-hero-action-btn">Help</a>
          )}

          <div className="launch-school-chip launch-hero-action-btn">{schoolName}</div>
          {userAvatar ? (
            <img
              src={userAvatar}
              alt={userInitials}
              className="launch-hero-avatar-img launch-hero-avatar"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.nextSibling.style.display = 'flex';
              }}
            />
          ) : null}
          <div
            className="launch-user-menu launch-hero-avatar"
            style={userAvatar ? { display: 'none' } : undefined}
          >
            {userInitials}
          </div>
        </div>
      </div>

      {/* ── Hero body ───────────────────────────────────────────────── */}
      <div className="launch-hero-body">
        <div className="launch-hero-text">
          <h1 className="launch-hero-title">{title}</h1>
        </div>

        {/* MS 365 quick-launch panel */}
        <div className="launch-hero-ms365">
          <div className="launch-hero-ms365-label">Quick launch</div>
          <div className="launch-hero-ms365-chips">
            <a
              href="https://teams.microsoft.com"
              target="_blank"
              rel="noreferrer"
              className="launch-ms-app-chip launch-ms-app-chip--teams"
              aria-label="Open Microsoft Teams"
            >
              <TeamsIcon /> Teams
            </a>
            <a
              href="https://outlook.office365.com"
              target="_blank"
              rel="noreferrer"
              className="launch-ms-app-chip launch-ms-app-chip--outlook"
              aria-label="Open Outlook"
            >
              <OutlookIcon /> Outlook
            </a>
            <a
              href="https://outlook.office365.com/calendar"
              target="_blank"
              rel="noreferrer"
              className="launch-ms-app-chip launch-ms-app-chip--calendar"
              aria-label="Open Calendar"
            >
              <CalendarIcon /> Calendar
            </a>
          </div>
          <div className="launch-hero-date" aria-label={`Today is ${today}`}>{today}</div>
        </div>
      </div>
    </div>
  );
}
