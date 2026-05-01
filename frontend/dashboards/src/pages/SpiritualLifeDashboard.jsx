import CrownLayout from '../components/crown/CrownLayout.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';

import PrayerRequests from '../components/dashboard/PrayerRequests.jsx';
import DailyDevotion from '../components/dashboard/DailyDevotion.jsx';
import SpecialDays from '../components/dashboard/SpecialDays.jsx';
import KpiCard from '../components/dashboard/KpiCard.jsx';
import KpiCardGrid from '../components/dashboard/KpiCardGrid.jsx';
import ProgressGoalCard from '../components/dashboard/ProgressGoalCard.jsx';
import HealthRingCard from '../components/dashboard/HealthRingCard.jsx';
import TrendChartCard from '../components/dashboard/TrendChartCard.jsx';

import StudentLifePrioritiesPanel from '../components/dashboard/studentlife/StudentLifePrioritiesPanel.jsx';
import StudentLifeAlertsPanel from '../components/dashboard/studentlife/StudentLifeAlertsPanel.jsx';
import StudentLifeActivityFeedCard from '../components/dashboard/studentlife/StudentLifeActivityFeedCard.jsx';
import StudentLifeSnapshotCard from '../components/dashboard/studentlife/StudentLifeSnapshotCard.jsx';
import StudentLifeCalendarCard from '../components/dashboard/studentlife/StudentLifeCalendarCard.jsx';
import StudentLifeCommunicationsCard from '../components/dashboard/studentlife/StudentLifeCommunicationsCard.jsx';
import StudentLifeReportsCard from '../components/dashboard/studentlife/StudentLifeReportsCard.jsx';

export default function SpiritualLifeDashboard() {
  return (
    <CrownLayout
      title="Student Life / Chaplain Dashboard"
      subtitle="Chapel, service, student care, spiritual formation, and pastoral visibility"
    >
      <DashboardSection title="Faith and Community">
        <CrownGrid>
          <Col span={3}><PrayerRequests /></Col>
          <Col span={6}><DailyDevotion /></Col>
          <Col span={3}><SpecialDays /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Chaplain Action">
        <CrownGrid>
          <Col span={3}><StudentLifePrioritiesPanel /></Col>

          <Col span={6}>
            <KpiCardGrid>
              <KpiCard title="Chapel Attendance" value="89%" trend="Strong this week" icon="CHP" tone="good" />
              <KpiCard title="Service Hours Logged" value="2,340" trend="+112 this week" icon="SRV" tone="good" />
              <KpiCard title="Care Referrals" value="6" trend="Monitor this week" icon="CAR" tone="warn" />
              <KpiCard title="Mentoring Follow-Ups" value="4" trend="Pending check-in" icon="MEN" tone="warn" />
            </KpiCardGrid>
          </Col>

          <Col span={3}><StudentLifeAlertsPanel /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Spiritual Health">
        <CrownGrid>
          <Col span={4}>
            <ProgressGoalCard
              title="Chapel Attendance Goal"
              current={89}
              goal={100}
              percentLabel="89%"
              detail="Current average chapel attendance rate"
              colorClass="var(--crown-brand)"
            />
          </Col>

          <Col span={4}>
            <ProgressGoalCard
              title="Service Hours Goal"
              current={2340}
              goal={3000}
              percentLabel="78%"
              detail="2,340 of 3,000 annual hours logged"
              colorClass="#059669"
            />
          </Col>

          <Col span={4}>
            <HealthRingCard
              title="Spiritual Health Index"
              percent={82}
              subtitle="Formation score"
              detail="Chapel and service participation are solid overall. More mentoring follow-up is needed with several students."
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Spiritual Trends">
        <CrownGrid>
          <Col span={6}>
            <TrendChartCard
              title="Chapel Attendance Trend"
              subtitle="Recent weekly attendance"
              labels={['Week 1', 'Week 2', 'Week 3', 'Week 4']}
              datasets={[
                {
                  label: 'Attendance %',
                  data: [86, 88, 89, 89],
                  borderColor: '#004687',
                },
              ]}
            />
          </Col>

          <Col span={6}>
            <TrendChartCard
              title="Service Participation Trend"
              subtitle="Weekly service involvement"
              labels={['Week 1', 'Week 2', 'Week 3', 'Week 4']}
              datasets={[
                {
                  label: 'Hours Logged',
                  data: [420, 510, 620, 790],
                  borderColor: '#004687',
                },
              ]}
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Care Detail">
        <CrownGrid>
          <Col span={4}><StudentLifeActivityFeedCard /></Col>
          <Col span={8}><StudentLifeSnapshotCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Events, Communications, and Reports">
        <CrownGrid>
          <Col span={4}><StudentLifeCalendarCard /></Col>
          <Col span={4}><StudentLifeCommunicationsCard /></Col>
          <Col span={4}><StudentLifeReportsCard /></Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
