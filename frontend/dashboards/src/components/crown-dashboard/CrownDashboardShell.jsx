import CrownSidebar from '../launch/CrownSidebar.jsx';
import CrownTopbar from '../launch/CrownTopbar.jsx';

export default function CrownDashboardShell({
  activePath,
  schoolName,
  user,
  updatesCount,
  rightRail,
  children,
}) {
  const shellClass = rightRail ? 'launch-shell has-right-rail' : 'launch-shell';

  return (
    <div className={shellClass}>
      <CrownSidebar activePath={activePath} user={user} />
      <main className="launch-main">
        <CrownTopbar schoolName={schoolName} userInitials={user?.initials} updatesCount={updatesCount} />
        {children}
      </main>
      {rightRail ? <aside className="launch-right-rail">{rightRail}</aside> : null}
    </div>
  );
}
