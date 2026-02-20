import CrownLayout from '../components/crown/CrownLayout.jsx';

export function HomeDashboard() {
  return (
    <CrownLayout title="Crown" subtitle="School management platform">
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 320 }}>
        {[
          ['/billing',       'Billing'],
          ['/financial-aid', 'Financial Aid'],
          ['/academics',     'Academics'],
          ['/classrooms',    'Classrooms'],
          ['/gradebook',     'Gradebook (Read-Only)'],
          ['/transcript',    'Transcript (Read-Only)'],
        ].map(([href, label]) => (
          <a
            key={href}
            href={href}
            className="crown-btn"
            style={{ justifyContent: 'flex-start' }}
          >
            {label} &rarr;
          </a>
        ))}
      </nav>
    </CrownLayout>
  );
}
