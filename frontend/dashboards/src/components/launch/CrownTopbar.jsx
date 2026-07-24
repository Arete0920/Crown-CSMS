import { Link, useInRouterContext } from 'react-router';

export default function CrownTopbar({
  schoolName = 'Heritage Christian Academy',
  updatesCount = 3,
  userInitials = 'SJ',
}) {
  const hasRouterContext = useInRouterContext();

  return (
    <div className="launch-topbar">
      <label className="launch-search">
        <span className="launch-search-icon" aria-hidden="true" />
        <input type="search" placeholder="Search students, workflows, and actions" aria-label="Search" />
      </label>

      <div className="launch-topbar-actions">
        {hasRouterContext ? (
          <Link to="/communications" className="launch-icon-button">Updates <span className="launch-counter">{updatesCount}</span></Link>
        ) : (
          <a href="/communications" className="launch-icon-button">Updates <span className="launch-counter">{updatesCount}</span></a>
        )}
        {hasRouterContext ? (
          <Link to="/settings" className="launch-icon-button">Help</Link>
        ) : (
          <a href="/settings" className="launch-icon-button">Help</a>
        )}
        <div className="launch-school-chip">{schoolName}</div>
        <div className="launch-user-menu">{userInitials}</div>
      </div>
    </div>
  );
}
