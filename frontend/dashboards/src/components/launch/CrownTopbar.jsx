export default function CrownTopbar({ schoolName = 'Heritage Christian Academy' }) {
  return (
    <div className="launch-topbar">
      <label className="launch-search">
        <span className="launch-search-icon" aria-hidden="true" />
        <input type="search" placeholder="Search dashboard, students, or actions" aria-label="Search" />
      </label>

      <div className="launch-topbar-actions">
        <button type="button" className="launch-icon-button">Notifications <span className="launch-counter">3</span></button>
        <button type="button" className="launch-icon-button">Help</button>
        <div className="launch-school-chip">{schoolName}</div>
        <div className="launch-user-menu">Sarah</div>
      </div>
    </div>
  );
}