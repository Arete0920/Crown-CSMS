import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

export function HomeDashboard() {
  return (
    <CrownLayout title="Crown" subtitle="School management platform">
      {/* CROWN_DASH_GRID_NORMALIZED */}
      <CrownGrid>
        <Col span={3}><CrownMetricCard label="Status" value="Healthy" hint="All systems nominal" /></Col>
        <Col span={3}><CrownMetricCard label="Today" value="Live" hint="Demo surface active" /></Col>
        <Col span={3}><CrownMetricCard label="Security" value="Enforced" hint="Tenant + RBAC gates" /></Col>
        <Col span={3}><CrownMetricCard label="Data" value="Seeded" hint="Realistic demo records" /></Col>

        <Col span={12}>
          <CrownCard title="Navigation" right={<span className="crown-pill">Crown Dashboard</span>}>
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
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
