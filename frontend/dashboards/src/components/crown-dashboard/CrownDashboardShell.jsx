import CrownSidebar from '../launch/CrownSidebar.jsx';
import CrownTopbar from '../launch/CrownTopbar.jsx';

export default function CrownDashboardShell({ activePath, schoolName, user, updatesCount, children }) {
  return (
    <div className="launch-shell">
      <CrownSidebar activePath={activePath} user={user} />
      <main className="launch-main">
        <CrownTopbar schoolName={schoolName} userInitials={user?.initials} updatesCount={updatesCount} />
        {children}
      </main>
    </div>
  );
}
