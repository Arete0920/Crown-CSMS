import CrownLayout from '../components/crown/CrownLayout.jsx';
import CrownCard from '../components/crown/CrownCard.jsx';
import CrownMetricCard from '../components/crown/CrownMetricCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';

function BulletList({ items }) {
  if (!items?.length) return <div style={{ opacity: 0.75 }}>No items.</div>;

  return (
    <ul style={{ margin: 0, paddingLeft: 18 }}>
      {items.map((item) => (
        <li key={item} style={{ marginBottom: 6 }}>
          {item}
        </li>
      ))}
    </ul>
  );
}

export default function ParentDashboard() {
  return (
    <CrownLayout title="Parent Dashboard" subtitle="Overview for family academics, finance, and communication">
      <CrownGrid>
        <Col span={3}><CrownMetricCard label="Attendance" value="98%" hint="This month" /></Col>
        <Col span={3}><CrownMetricCard label="Progress" value="B+" hint="Across active courses" /></Col>
        <Col span={3}><CrownMetricCard label="Balance" value="$420" hint="Current amount due" /></Col>
        <Col span={3}><CrownMetricCard label="Alerts" value="2" hint="Needs review" /></Col>

        <Col span={8}>
          <CrownCard title="This Week">
            <BulletList
              items={[
                'Mon: Chapel at 8:30 AM',
                'Wed: Early dismissal at 1:30 PM',
                'Fri: Spirit day reminder',
              ]}
            />
          </CrownCard>
        </Col>

        <Col span={4}>
          <CrownCard title="Needs Attention">
            <BulletList
              items={[
                'Permission slip pending',
                'Unread teacher message',
              ]}
            />
          </CrownCard>
        </Col>

        <Col span={12}>
          <CrownCard title="Quick Links">
            <nav style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <a className="crown-btn" href="/academics/parent-snapshot">Parent Snapshot</a>
              <a className="crown-btn" href="/parent/attendance">Attendance</a>
              <a className="crown-btn" href="/finance/invoices">Invoices</a>
              <a className="crown-btn" href="/communications">Messages</a>
            </nav>
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
