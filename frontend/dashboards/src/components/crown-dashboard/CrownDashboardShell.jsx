import CrownSidebar from '../launch/CrownSidebar.jsx';
import CrownTopbar from '../launch/CrownTopbar.jsx';

export default function CrownDashboardShell({ activePath, schoolName, children }) {
  return (
    <div className="launch-shell">
      <CrownSidebar activePath={activePath} />
      <main className="launch-main">
        <CrownTopbar schoolName={schoolName} />
        {children}
      </main>
    </div>
  );
}
