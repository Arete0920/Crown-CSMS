import { Link, useInRouterContext } from 'react-router-dom';

const NAV_SECTIONS = [
  {
    title: 'Command center',
    items: [
      { label: 'Dashboard', href: '/dashboard', glyph: 'D' },
      { label: 'School', href: '/school-admin', glyph: 'S' },
      { label: 'Administration', href: '/admin', glyph: 'A' },
      { label: 'Reports', href: '/reporting', glyph: 'R' },
    ],
  },
  {
    title: 'Academic operations',
    items: [
      { label: 'Admissions', href: '/admissions', glyph: 'Ad' },
      { label: 'Academics', href: '/gradebook', glyph: 'Ac' },
      { label: 'Student Life', href: '/student-life', glyph: 'SL' },
      { label: 'Attendance', href: '/attendance', glyph: 'At' },
    ],
  },
  {
    title: 'Business and comms',
    items: [
      { label: 'Finance', href: '/finance', glyph: 'F' },
      { label: 'Communications', href: '/communications', glyph: 'C' },
      { label: 'Settings', href: '/settings', glyph: 'Se' },
    ],
  },
];

function BrandLockup() {
  return (
    <div className="launch-brand-lockup">
      <img
        src="/brand/crown-mark-transparent.svg"
        alt=""
        className="launch-brand-mark"
        aria-hidden="true"
        width="44"
        height="44"
      />
      <div>
        <img
          src="/brand/crown-logo-transparent.svg"
          alt=""
          aria-hidden="true"
          className="launch-brand-logo"
          height="36"
        />
        <span className="sr-only">CROWN</span>
        <span className="sr-only">Christian School Management Solution</span>
        <div className="launch-brand-edition">Administrator Command Center</div>
      </div>
    </div>
  );
}

export default function CrownSidebar({
  activePath = '/dashboard',
  user = { initials: 'SJ', name: 'Sarah James', role: 'Head of School' },
}) {
  const hasRouterContext = useInRouterContext();

  return (
    <aside className="launch-sidebar">
      <BrandLockup />

      <nav className="launch-sidebar-nav" aria-label="Primary">
        {NAV_SECTIONS.map((section) => (
          <section key={section.title} className="launch-nav-section" aria-label={section.title}>
            <h3>{section.title}</h3>
            <div className="launch-nav-section-items">
              {section.items.map((item) => {
                const active = activePath === item.href;
                const classes = active ? 'is-active' : '';
                const content = (
                  <>
                    <span className="launch-nav-icon" aria-hidden="true">{item.glyph}</span>
                    <span>{item.label}</span>
                  </>
                );

                if (hasRouterContext) {
                  return (
                    <Link key={item.href + item.label} to={item.href} className={classes}>
                      {content}
                    </Link>
                  );
                }

                return (
                  <a key={item.href + item.label} href={item.href} className={classes}>
                    {content}
                  </a>
                );
              })}
            </div>
          </section>
        ))}
      </nav>

      <div className="launch-user-card">
        <div className="launch-user-avatar">{user.initials || 'SJ'}</div>
        <div>
          <div className="launch-user-name">{user.name || 'Sarah James'}</div>
          <div className="launch-user-role">{user.role || 'Head of School'}</div>
        </div>
      </div>
    </aside>
  );
}
