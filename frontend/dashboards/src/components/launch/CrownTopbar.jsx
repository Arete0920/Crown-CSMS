export default function CrownTopbar({
  schoolName = 'Heritage Christian Academy',
  updatesCount = 3,
  userInitials = 'SJ',
}) {
  return (
    <div className="launch-topbar">
      <label className="launch-search">
        <span className="launch-search-icon" aria-hidden="true" />
        <input type="search" placeholder="Search students, workflows, and actions" aria-label="Search" />
      </label>

      <div className="launch-topbar-actions">
        <div className="launch-chip launch-chip-muted">School day live</div>
        <button type="button" className="launch-icon-button">Updates <span className="launch-counter">{updatesCount}</span></button>
        <button type="button" className="launch-icon-button">Help</button>
        <div className="launch-school-chip">{schoolName}</div>
        <div className="launch-user-menu">
          <span className="launch-user-menu-avatar">{userInitials}</span>
          <span className="launch-user-menu-label">Admin</span>
        </div>
      </div>
    </div>
  );
}
