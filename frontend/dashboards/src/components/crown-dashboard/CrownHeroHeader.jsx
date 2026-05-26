import { Link, useInRouterContext } from 'react-router-dom';
import CrownLogo from '../brand/CrownLogo';
import MicrosoftProductLogo from '../brand/MicrosoftProductLogo';

/* ── CrownHeroHeader ──────────────────────────────────────────────────── */

export default function CrownHeroHeader({
  schoolName = 'Heritage Christian Academy',
  updatesCount = 3,
  userInitials = 'SJ',
  userAvatar = null,
  title,
  heroMessage = null,
}) {
  const hasRouterContext = useInRouterContext();

  return (
    <header className="launch-hero-header">
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

        <div className="launch-topbar-actions launch-hero-topbar-actions">
          <div className="launch-school-chip launch-hero-action-btn">{schoolName}</div>

          {hasRouterContext ? (
            <Link to="/settings" className="launch-icon-button launch-hero-action-btn">Help</Link>
          ) : (
            <a href="/settings" className="launch-icon-button launch-hero-action-btn">Help</a>
          )}

          {hasRouterContext ? (
            <Link to="/communications" className="launch-icon-button launch-hero-action-btn">
              Updates <span className="launch-counter">{updatesCount}</span>
            </Link>
          ) : (
            <a href="/communications" className="launch-icon-button launch-hero-action-btn">
              Updates <span className="launch-counter">{updatesCount}</span>
            </a>
          )}
        </div>
      </div>

      {/* ── Hero body ───────────────────────────────────────────────── */}
      <div className="launch-hero-body">
        {/* Left: content stack */}
        <div className="launch-hero-content">
          <div className="launch-hero-brand">
            <CrownLogo placement="dashboardHero" />
          </div>

          <div className="launch-hero-text">
            <h1 className="launch-hero-title">{title}</h1>
            {heroMessage && (
              <p className="launch-hero-message">{heroMessage}</p>
            )}
          </div>

          {/* MS 365 quick-launch */}
          <div className="launch-hero-ms365-center">
            <div className="launch-hero-ms365-chips">
              <a
                href="https://teams.microsoft.com"
                target="_blank"
                rel="noreferrer"
                className="launch-ms-app-chip launch-ms-app-chip--teams"
                aria-label="Open Microsoft Teams"
              >
                <MicrosoftProductLogo product="teams" label="Teams" />
              </a>
              <a
                href="https://outlook.office365.com"
                target="_blank"
                rel="noreferrer"
                className="launch-ms-app-chip launch-ms-app-chip--outlook"
                aria-label="Open Outlook"
              >
                <MicrosoftProductLogo product="outlook" label="Outlook" />
              </a>
              <a
                href="https://outlook.office365.com/calendar"
                target="_blank"
                rel="noreferrer"
                className="launch-ms-app-chip launch-ms-app-chip--calendar"
                aria-label="Open Calendar"
              >
                <MicrosoftProductLogo product="microsoft365" label="Calendar" />
              </a>
              <a
                href="https://word.office.com"
                target="_blank"
                rel="noreferrer"
                className="launch-ms-app-chip launch-ms-app-chip--word"
                aria-label="Open Word"
              >
                <MicrosoftProductLogo product="word" label="Word" />
              </a>
              <a
                href="https://excel.office.com"
                target="_blank"
                rel="noreferrer"
                className="launch-ms-app-chip launch-ms-app-chip--excel"
                aria-label="Open Excel"
              >
                <MicrosoftProductLogo product="excel" label="Excel" />
              </a>
              <a
                href="https://onedrive.live.com"
                target="_blank"
                rel="noreferrer"
                className="launch-ms-app-chip launch-ms-app-chip--onedrive"
                aria-label="Open OneDrive"
              >
                <MicrosoftProductLogo product="onedrive" label="OneDrive" />
              </a>
            </div>
          </div>
        </div>

        {/* Right: avatar */}
        {userAvatar ? (
          <img
            src={userAvatar}
            alt={userInitials}
            className="launch-hero-avatar-img"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        ) : null}
      </div>
    </header>
  );
}
