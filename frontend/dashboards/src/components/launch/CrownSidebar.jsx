const NAV_ITEMS = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'School', href: '/school-admin' },
  { label: 'Administration', href: '/admin' },
  { label: 'Admissions', href: '/admissions' },
  { label: 'Academics', href: '/gradebook' },
  { label: 'Student Life', href: '/attendance' },
  { label: 'Attendance', href: '/attendance' },
  { label: 'Finance', href: '/finance' },
  { label: 'Communications', href: '/communications' },
  { label: 'Reports', href: '/dashboard' },
  { label: 'Settings', href: '/dashboard' },
];

function BrandLockup() {
  return (
    <div className="launch-brand-lockup">
      <div className="launch-brand-crest" aria-hidden="true">
        <div className="launch-brand-crest-inner" />
      </div>
      <div>
        <div className="launch-brand-title">CROWN</div>
        <div className="launch-brand-tagline">Christian School Management Solution</div>
      </div>
    </div>
  );
}

export default function CrownSidebar({ activePath = '/dashboard' }) {
  return (
    <aside className="launch-sidebar">
      <BrandLockup />

      <nav className="launch-sidebar-nav" aria-label="Primary">
        {NAV_ITEMS.map((item) => {
          const active = activePath === item.href;
          return (
            <a key={item.href + item.label} href={item.href} className={active ? 'is-active' : ''}>
              <span className="launch-nav-icon" aria-hidden="true" />
              <span>{item.label}</span>
            </a>
          );
        })}
      </nav>

      <div className="launch-user-card">
        <div className="launch-user-avatar">SJ</div>
        <div>
          <div className="launch-user-name">Sarah James</div>
          <div className="launch-user-role">Head of School</div>
        </div>
      </div>
    </aside>
  );
}