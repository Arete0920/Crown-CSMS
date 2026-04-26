import CrownSidebar from './CrownSidebar.jsx';
import CrownTopbar from './CrownTopbar.jsx';
import CrownPageHeader from './CrownPageHeader.jsx';

export default function CrownLaunchShell({ activePath, eyebrow, title, subtitle, note, children }) {
  return (
    <div className="launch-shell">
      <CrownSidebar activePath={activePath} />

      <main className="launch-main">
        <CrownTopbar />
        <CrownPageHeader eyebrow={eyebrow} title={title} subtitle={subtitle} note={note} />
        <div className="launch-content">{children}</div>
      </main>
    </div>
  );
}