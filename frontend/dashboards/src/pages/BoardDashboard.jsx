import CrownLayout from '../components/crown/CrownLayout.jsx';
import { KpiStrip } from '../components/dashboard/KpiFlipCard.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';

import PrayerRequests from '../components/dashboard/PrayerRequests.jsx';
import DailyDevotion from '../components/dashboard/DailyDevotion.jsx';
import SpecialDays from '../components/dashboard/SpecialDays.jsx';
import FlipMetricCard from '../components/dashboard/FlipMetricCard.jsx';
import KpiCard from '../components/dashboard/KpiCard.jsx';
import KpiCardGrid from '../components/dashboard/KpiCardGrid.jsx';
import ProgressGoalCard from '../components/dashboard/ProgressGoalCard.jsx';
import HealthRingCard from '../components/dashboard/HealthRingCard.jsx';
import TrendChartCard from '../components/dashboard/TrendChartCard.jsx';

import BoardPrioritiesPanel from '../components/dashboard/board/BoardPrioritiesPanel.jsx';
import BoardAlertsPanel from '../components/dashboard/board/BoardAlertsPanel.jsx';
import BoardActivityFeedCard from '../components/dashboard/board/BoardActivityFeedCard.jsx';
import BoardStrategicSnapshotCard from '../components/dashboard/board/BoardStrategicSnapshotCard.jsx';
import BoardCalendarCard from '../components/dashboard/board/BoardCalendarCard.jsx';
import BoardCommunicationsCard from '../components/dashboard/board/BoardCommunicationsCard.jsx';
import BoardReportSnapshotCard from '../components/dashboard/board/BoardReportSnapshotCard.jsx';

const BOARD_KPI = [
  { label: 'Total Enrollment', value: '—', trend: null, trendUp: null,
    definition: 'Total enrolled students across all campuses for the current school year.',
    dataSource: 'Enrollment Summary', dataHref: '/admissions' },
  { label: 'Revenue YTD',     value: '—', trend: null, trendUp: null,
    definition: 'Total revenue collected year-to-date against annual budget.',
    dataSource: 'Finance API', dataHref: '/finance' },
  { label: 'Retention Rate',  value: '—', trend: null, trendUp: null,
    definition: 'Percentage of students returning from the prior school year.',
    dataSource: 'Student Records', dataHref: '/academics' },
  { label: 'Advancement Total', value: '—', trend: null, trendUp: null,
    definition: 'Total advancement and giving received year-to-date.',
    dataSource: 'Advancement API', dataHref: '/advancement' },
];

export default function BoardDashboard() {
  return (
    <CrownLayout
      title="Board Dashboard"
      kpiStrip={<KpiStrip cards={BOARD_KPI} />}
      subtitle="Strategic oversight, institutional health, and governance visibility"
    >
      <DashboardSection title="Faith and Community">
        <CrownGrid>
          <Col span={3}><PrayerRequests /></Col>
          <Col span={6}><DailyDevotion /></Col>
          <Col span={3}><SpecialDays /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Board Snapshot">
        <CrownGrid>
          <Col span={3}><BoardPrioritiesPanel /></Col>

          <Col span={6}>
            <KpiCardGrid>
              <KpiCard title="Enrollment" value="412" trend="+4% vs last year" icon="ENR" tone="good" />
              <KpiCard title="Revenue Collected" value="$3.1M" trend="+6% YTD" icon="REV" tone="good" />

              <FlipMetricCard
                title="Retention Rate"
                value="92%"
                trend="+2% vs prior year"
                definition="Percentage of returning students compared to prior-year enrollment, excluding graduates."
                sources={['Enrollment Summary', 'Student Records', 'Year-End Roster']}
                links={['View Board Report', 'Open Retention Summary', 'Download Packet']}
              />

              <FlipMetricCard
                title="Mission Engagement"
                value="81%"
                trend="Healthy overall"
                definition="Composite indicator based on service participation, chapel engagement, and schoolwide mission activities."
                sources={['Service Hours', 'Chapel Attendance', 'Student Life Reports']}
                links={['Open Mission Summary', 'View Engagement Report', 'Export Data']}
              />
            </KpiCardGrid>
          </Col>

          <Col span={3}><BoardAlertsPanel /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Strategic Health">
        <CrownGrid>
          <Col span={4}>
            <ProgressGoalCard
              title="Enrollment Goal"
              current={412}
              goal={450}
              percentLabel="91%"
              detail="412 of 450 enrolled students"
              colorClass="var(--crown-brand)"
            />
          </Col>

          <Col span={4}>
            <ProgressGoalCard
              title="Revenue Goal"
              current={3100000}
              goal={3300000}
              percentLabel="94%"
              detail="$3.1M of $3.3M collected"
              colorClass="#059669"
            />
          </Col>

          <Col span={4}>
            <HealthRingCard
              title="Board Health Index"
              percent={87}
              subtitle="Institutional score"
              detail="The school remains stable in enrollment, finance, and mission engagement, with continued attention needed in grade-level retention."
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Strategic Analysis">
        <CrownGrid>
          <Col span={6}>
            <TrendChartCard
              title="Enrollment Trend"
              subtitle="Current year vs prior year"
              labels={['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']}
              datasets={[
                {
                  label: 'Current Year',
                  data: [365, 374, 382, 391, 397, 403, 409, 412],
                  borderColor: '#004687',
                },
                {
                  label: 'Prior Year',
                  data: [352, 360, 367, 375, 382, 389, 393, 396],
                  borderColor: '#C4A65A',
                },
              ]}
            />
          </Col>

          <Col span={6}>
            <TrendChartCard
              title="Revenue Trend"
              subtitle="Collected revenue this year vs prior year"
              labels={['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']}
              datasets={[
                {
                  label: 'Current Year',
                  data: [240000, 410000, 695000, 980000, 1410000, 1960000, 2520000, 3100000],
                  borderColor: '#004687',
                },
                {
                  label: 'Prior Year',
                  data: [220000, 390000, 650000, 920000, 1320000, 1840000, 2360000, 2890000],
                  borderColor: '#C4A65A',
                },
              ]}
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Governance Detail">
        <CrownGrid>
          <Col span={4}><BoardActivityFeedCard /></Col>
          <Col span={8}><BoardStrategicSnapshotCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Board Awareness">
        <CrownGrid>
          <Col span={4}><BoardCalendarCard /></Col>
          <Col span={4}><BoardCommunicationsCard /></Col>
          <Col span={4}><BoardReportSnapshotCard /></Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
