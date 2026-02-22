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

export default function StudentDashboard() {
  return (
    <CrownLayout title="Student Dashboard" subtitle="Today view for classes, assignments, and alerts">
      <CrownGrid>
        <Col span={3}><CrownMetricCard label="Attendance" value="Present" hint="No flags today" /></Col>
        <Col span={3}><CrownMetricCard label="Assignments" value="2" hint="Due this week" /></Col>
        <Col span={3}><CrownMetricCard label="Progress" value="B+" hint="Current average" /></Col>
        <Col span={3}><CrownMetricCard label="Messages" value="1" hint="Unread" /></Col>

        <Col span={8}>
          <CrownCard title="Today">
            <BulletList
              items={[
                'Block 1: English',
                'Block 2: Algebra',
                'Block 3: Bible',
                'Block 4: History',
              ]}
            />
          </CrownCard>
        </Col>

        <Col span={4}>
          <CrownCard title="Messages & Alerts">
            <BulletList
              items={[
                'Reminder: chapel dress code',
                'New teacher announcement',
              ]}
            />
          </CrownCard>
        </Col>

        <Col span={12}>
          <CrownCard title="Quick Links">
            <nav style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <a className="crown-btn" href="/gradebook">Gradebook</a>
              <a className="crown-btn" href="/transcript">Transcript</a>
              <a className="crown-btn" href="/academics/student-work">Student Work</a>
              <a className="crown-btn" href="/communications">Messages</a>
            </nav>
          </CrownCard>
        </Col>
      </CrownGrid>
    </CrownLayout>
  );
}
