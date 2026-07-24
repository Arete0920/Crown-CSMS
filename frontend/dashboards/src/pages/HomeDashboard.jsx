import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import { Link } from 'react-router';

export function HomeDashboard() {
  const navLinks = [
    ['/billing', 'Billing'],
    ['/financial-aid', 'Financial Aid'],
    ['/academics', 'Academics'],
    ['/classrooms', 'Classrooms'],
    ['/gradebook', 'Gradebook (Read-Only)'],
    ['/transcript', 'Transcript (Read-Only)'],
  ];

  return (
    <CrownLayout title="Crown" subtitle="School management platform">
      <h1 className="text-2xl font-semibold tracking-tight">Crown Dashboard</h1>

      <section aria-labelledby="proof-links-heading" style={{ marginBottom: 16 }}>
        <h2 id="proof-links-heading">Proof Links</h2>
        <nav aria-label="Proof routes">
          <ul>
            <li><Link to="/admin">Administration</Link></li>
            <li><Link to="/teacher">Teacher</Link></li>
            <li><Link to="/parent">Parent</Link></li>
            <li><Link to="/gradebook">Gradebook</Link></li>
            <li><Link to="/login">Login</Link></li>
          </ul>
        </nav>
      </section>

      {/* CROWN_DASH_GRID_NORMALIZED */}
      <CrownGrid>
        <Col span={3}><CrownMetricCard label="Status" value="Healthy" hint="All systems nominal" /></Col>
        <Col span={3}><CrownMetricCard label="Today" value="Live" hint="Demo surface active" /></Col>
        <Col span={3}><CrownMetricCard label="Security" value="Enforced" hint="Tenant + RBAC gates" /></Col>
        <Col span={3}><CrownMetricCard label="Data" value="Seeded" hint="Realistic demo records" /></Col>

        <Col span={12}>
          <CrownCard title="Navigation" right={<span className="crown-pill">Crown Dashboard</span>}>
            <div style={{ marginBottom: 12, color: 'var(--crown-muted)', fontSize: 13 }}>
              Start from a core workspace. All destinations below are canonical live routes.
            </div>

            <nav
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: 10,
                maxWidth: 760,
              }}
            >
              {navLinks.map(([href, label]) => (
                <a
                  key={href}
                  href={href}
                  className="crown-btn"
                  style={{ justifyContent: 'space-between', minHeight: 44 }}
                >
                  {label} &rarr;
                </a>
              ))}
            </nav>
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
