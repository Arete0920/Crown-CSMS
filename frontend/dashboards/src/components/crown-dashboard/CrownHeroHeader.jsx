import { useEffect, useState } from 'react';
import { Link, useInRouterContext } from 'react-router';
import CrownLogo from '../brand/CrownLogo';
import MicrosoftProductLogo from '../brand/MicrosoftProductLogo';
import CrownIcon from '../icons/CrownIcon.jsx';

const MICROSOFT_SHORTCUTS = [
  { product: 'teams', label: 'Microsoft Teams', href: 'https://teams.microsoft.com/v2/' },
  { product: 'outlook', label: 'Microsoft Outlook', href: 'https://outlook.office.com/mail/' },
  { product: 'word', label: 'Microsoft Word', href: 'https://www.microsoft365.com/launch/word' },
  { product: 'excel', label: 'Microsoft Excel', href: 'https://www.microsoft365.com/launch/excel' },
  { product: 'onedrive', label: 'Microsoft OneDrive', href: 'https://www.microsoft365.com/launch/onedrive' },
];

export default function CrownHeroHeader({
  schoolName = 'Heritage Christian Academy',
  updatesCount = 3,
  userInitials = 'SJ',
  userAvatar = null,
  title,
  heroMessage = null,
}) {
  const hasRouterContext = useInRouterContext();
  const [avatarFailed, setAvatarFailed] = useState(false);

  useEffect(() => {
    setAvatarFailed(false);
  }, [userAvatar]);

  return (
    <header className="launch-hero-header">
      <div className="launch-hero-topbar">
        <label className="launch-search launch-hero-search" aria-label="Search">
          <CrownIcon name="search" size={18} className="launch-search-svg" />
          <input
            type="search"
            placeholder="Search students, workflows, and actions"
            aria-label="Search students, workflows, and actions"
          />
        </label>

        <div className="launch-topbar-actions launch-hero-topbar-actions">
          <div className="launch-school-chip launch-hero-action-btn">{schoolName}</div>

          {hasRouterContext ? (
            <Link to="/settings" className="launch-icon-button launch-hero-action-btn">
              <CrownIcon name="help" size={17} />
              Help
            </Link>
          ) : (
            <a href="/settings" className="launch-icon-button launch-hero-action-btn">
              <CrownIcon name="help" size={17} />
              Help
            </a>
          )}

          {hasRouterContext ? (
            <Link to="/communications" className="launch-icon-button launch-hero-action-btn">
              <CrownIcon name="updates" size={17} />
              Updates <span className="launch-counter">{updatesCount}</span>
            </Link>
          ) : (
            <a href="/communications" className="launch-icon-button launch-hero-action-btn">
              <CrownIcon name="updates" size={17} />
              Updates <span className="launch-counter">{updatesCount}</span>
            </a>
          )}
        </div>
      </div>

      <div className="launch-hero-body">
        <div className="launch-hero-content">
          <div className="launch-hero-brand">
            <CrownLogo placement="dashboardHero" />
          </div>

          <div className="launch-hero-text">
            <h1 className="launch-hero-title">{title}</h1>
            {heroMessage ? <p className="launch-hero-message">{heroMessage}</p> : null}
          </div>
        </div>

        <div className="launch-hero-user" aria-label={`Signed in as ${userInitials}`}>
          {userAvatar && !avatarFailed ? (
            <img
              src={userAvatar}
              alt=""
              className="launch-hero-avatar-img"
              onError={() => setAvatarFailed(true)}
            />
          ) : (
            <span className="launch-hero-user-avatar">{userInitials}</span>
          )}
          <span className="launch-hero-user-label">Your workspace</span>
        </div>
      </div>

      <section className="launch-m365-panel" aria-label="Microsoft 365 Education shortcuts">
        <div className="launch-m365-heading">
          <span className="launch-m365-kicker">Microsoft 365 Education</span>
          <span className="launch-m365-note">Connected tools for communication and productivity</span>
        </div>
        <div className="launch-m365-shortcuts">
          {MICROSOFT_SHORTCUTS.map((shortcut) => (
            <a
              key={shortcut.product}
              href={shortcut.href}
              target="_blank"
              rel="noopener noreferrer"
              className="launch-m365-shortcut"
              aria-label={`Open ${shortcut.label}`}
            >
              <span className="launch-m365-shortcut-icon" aria-hidden="true">
                <MicrosoftProductLogo
                  product={shortcut.product}
                  label={shortcut.label}
                  compactFallback
                  decorative
                />
              </span>
              <span>{shortcut.label}</span>
            </a>
          ))}
        </div>
      </section>
    </header>
  );
}
