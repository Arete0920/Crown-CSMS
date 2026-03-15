import CrownLayout from '../components/crown/CrownLayout.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';

import DailyDevotion from '../components/dashboard/DailyDevotion.jsx';
import SpecialDays from '../components/dashboard/SpecialDays.jsx';
import KpiCard from '../components/dashboard/KpiCard.jsx';
import KpiCardGrid from '../components/dashboard/KpiCardGrid.jsx';
import ProgressGoalCard from '../components/dashboard/ProgressGoalCard.jsx';
import HealthRingCard from '../components/dashboard/HealthRingCard.jsx';
import TrendChartCard from '../components/dashboard/TrendChartCard.jsx';

import ParentAtAGlanceCard from '../components/dashboard/parent/ParentAtAGlanceCard.jsx';
import ParentPrioritiesPanel from '../components/dashboard/parent/ParentPrioritiesPanel.jsx';
import ParentAlertsPanel from '../components/dashboard/parent/ParentAlertsPanel.jsx';
import ParentActivityFeedCard from '../components/dashboard/parent/ParentActivityFeedCard.jsx';
import ParentChildrenSnapshotCard from '../components/dashboard/parent/ParentChildrenSnapshotCard.jsx';
import ParentCalendarCard from '../components/dashboard/parent/ParentCalendarCard.jsx';
import ParentMessagesCard from '../components/dashboard/parent/ParentMessagesCard.jsx';
import ParentReportsCard from '../components/dashboard/parent/ParentReportsCard.jsx';

export default function ParentDashboard() {
  return (
    <CrownLayout
      title="Parent Portal"
      subtitle="Your children, assignments, attendance, tuition, messages, and family events"
    >
      <h1 className="text-2xl font-semibold tracking-tight">Parent Dashboard</h1>

      <DashboardSection title="Daily Mission and Family Snapshot">
        <CrownGrid>
          <Col span={6}><DailyDevotion /></Col>
          <Col span={3}><SpecialDays /></Col>
          <Col span={3}><ParentAtAGlanceCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Family Action">
        <CrownGrid>
          <Col span={3}><ParentPrioritiesPanel /></Col>

          <Col span={6}>
            <KpiCardGrid>
              <KpiCard title="Household Balance" value="$620" trend="Current balance" icon="BIL" tone="default" />
              <KpiCard title="Children" value="2" trend="In active classes" icon="FAM" tone="good" />
              <KpiCard title="Missing Assignments" value="7" trend="Across all children" icon="ASN" tone="warn" />
              <KpiCard title="Upcoming" value="5" trend="Events and due dates" icon="CAL" tone="good" />
            </KpiCardGrid>
          </Col>

          <Col span={3}><ParentAlertsPanel /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Family Health">
        <CrownGrid>
          <Col span={4}>
            <ProgressGoalCard
              title="Tuition Progress"
              current={9380}
              goal={10000}
              percentLabel="94%"
              detail="$9,380 of $10,000 paid"
              colorClass="var(--crown-brand)"
            />
          </Col>

          <Col span={4}>
            <ProgressGoalCard
              title="Assignment Completion"
              current={86}
              goal={100}
              percentLabel="86%"
              detail="Current work completion across children"
              colorClass="#059669"
            />
          </Col>

          <Col span={4}>
            <HealthRingCard
              title="Student Wellness"
              percent={89}
              subtitle="Family overview"
              detail="Attendance and participation are healthy overall. One student needs assignment follow-up."
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Family Trends">
        <CrownGrid>
          <Col span={6}>
            <TrendChartCard
              title="Grades Trend"
              subtitle="Recent grade movement"
              labels={['Week 1', 'Week 2', 'Week 3', 'Week 4']}
              datasets={[
                {
                  label: 'Average Grade',
                  data: [87, 89, 88, 90],
                  borderColor: '#004687',
                },
              ]}
            />
          </Col>

          <Col span={6}>
            <TrendChartCard
              title="Attendance Trend"
              subtitle="Recent family attendance pattern"
              labels={['Week 1', 'Week 2', 'Week 3', 'Week 4']}
              datasets={[
                {
                  label: 'Attendance %',
                  data: [96, 95, 97, 96],
                  borderColor: '#004687',
                },
              ]}
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Recent Family Detail">
        <CrownGrid>
          <Col span={4}><ParentActivityFeedCard /></Col>
          <Col span={8}><ParentChildrenSnapshotCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Events, Messages, and Reports">
        <CrownGrid>
          <Col span={4}><ParentCalendarCard /></Col>
          <Col span={4}><ParentMessagesCard /></Col>
          <Col span={4}><ParentReportsCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Quick Links">
        <CrownGrid>
          <Col span={6}><a href="/academics/parent-snapshot">Academics Snapshot</a></Col>
          <Col span={6}><a href="/finance/invoices">Finance Invoices</a></Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
