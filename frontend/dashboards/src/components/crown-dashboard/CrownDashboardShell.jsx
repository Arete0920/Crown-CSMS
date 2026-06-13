import PropTypes from 'prop-types';
import CrownSidebar from '../launch/CrownSidebar.jsx';
import CrownTopbar from '../launch/CrownTopbar.jsx';

export default function CrownDashboardShell({
  activePath,
  schoolName,
  user,
  updatesCount,
  rightRail,
  children,
  topbarSlot,
}) {
  const shellClass = rightRail ? 'launch-shell has-right-rail' : 'launch-shell';

  return (
    <div className={shellClass}>
      <CrownSidebar activePath={activePath} user={user} />
      <main className="launch-main">
        {topbarSlot ?? <CrownTopbar schoolName={schoolName} userInitials={user?.initials} updatesCount={updatesCount} />}
        {children}
      </main>
      {rightRail ? <aside className="launch-right-rail">{rightRail}</aside> : null}
    </div>
  );
}

CrownDashboardShell.propTypes = {
  activePath: PropTypes.string,
  schoolName: PropTypes.string,
  user: PropTypes.shape({ initials: PropTypes.string }),
  updatesCount: PropTypes.number,
  rightRail: PropTypes.node,
  children: PropTypes.node,
  topbarSlot: PropTypes.node,
};
