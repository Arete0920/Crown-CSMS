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

import TeacherAtAGlanceCard from '../components/dashboard/teacher/TeacherAtAGlanceCard.jsx';
import TeacherPrioritiesPanel from '../components/dashboard/teacher/TeacherPrioritiesPanel.jsx';
import TeacherAlertsPanel from '../components/dashboard/teacher/TeacherAlertsPanel.jsx';
import TeacherActivityFeedCard from '../components/dashboard/teacher/TeacherActivityFeedCard.jsx';
import TeacherClassSnapshotCard from '../components/dashboard/teacher/TeacherClassSnapshotCard.jsx';
import TeacherScheduleCard from '../components/dashboard/teacher/TeacherScheduleCard.jsx';
import TeacherMessagesCard from '../components/dashboard/teacher/TeacherMessagesCard.jsx';
import TeacherShortcutsCard from '../components/dashboard/teacher/TeacherShortcutsCard.jsx';

export default function TeacherDashboard() {
  return (
    <CrownLayout
      title="Teacher Dashboard"
      subtitle="Classes, attendance, grading, messages, and daily classroom execution"
    >
      <DashboardSection title="Daily Mission and Classroom Snapshot">
        <CrownGrid>
          <Col span={6}><DailyDevotion /></Col>
          <Col span={3}><SpecialDays /></Col>
          <Col span={3}><TeacherAtAGlanceCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Teacher Action">
        <CrownGrid>
          <Col span={3}><TeacherPrioritiesPanel /></Col>

          <Col span={6}>
            <KpiCardGrid>
              <KpiCard title="Classes Today" value="5" trend="Full teaching day" icon="CLS" tone="default" />
              <KpiCard title="Attendance Submitted" value="4/5" trend="1 class remaining" icon="ATT" tone="warn" />
              <KpiCard title="Assignments to Grade" value="23" trend="Manage by end of day" icon="GRD" tone="warn" />
              <KpiCard title="Parent Messages" value="3" trend="Unread this morning" icon="MSG" tone="warn" />
            </KpiCardGrid>
          </Col>

          <Col span={3}><TeacherAlertsPanel /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Classroom Health">
        <CrownGrid>
          <Col span={4}>
            <ProgressGoalCard
              title="Attendance Completion"
              current={4}
              goal={5}
              percentLabel="80%"
              detail="4 of 5 class attendance entries submitted"
              colorClass="var(--crown-brand)"
            />
          </Col>

          <Col span={4}>
            <ProgressGoalCard
              title="Grading Progress"
              current={77}
              goal={100}
              percentLabel="77%"
              detail="77% of current assignments graded"
              colorClass="#059669"
            />
          </Col>

          <Col span={4}>
            <HealthRingCard
              title="Classroom Health"
              percent={83}
              subtitle="Class status"
              detail="Attendance and assignment completion are healthy overall. One class section needs follow-up."
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Class Analysis">
        <CrownGrid>
          <Col span={6}>
            <TrendChartCard
              title="Attendance Trend"
              subtitle="Average attendance this week"
              labels={['Mon', 'Tue', 'Wed', 'Thu', 'Fri']}
              datasets={[
                {
                  label: 'Attendance %',
                  data: [95, 94, 96, 92, 93],
                  borderColor: '#004687',
                },
              ]}
            />
          </Col>

          <Col span={6}>
            <TrendChartCard
              title="Assignment Completion Trend"
              subtitle="Student completion by day"
              labels={['Mon', 'Tue', 'Wed', 'Thu', 'Fri']}
              datasets={[
                {
                  label: 'Completion %',
                  data: [84, 82, 88, 79, 85],
                  borderColor: '#004687',
                },
              ]}
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Operational Detail">
        <CrownGrid>
          <Col span={4}><TeacherActivityFeedCard /></Col>
          <Col span={8}><TeacherClassSnapshotCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Schedule, Messages, and Shortcuts">
        <CrownGrid>
          <Col span={4}><TeacherScheduleCard /></Col>
          <Col span={4}><TeacherMessagesCard /></Col>
          <Col span={4}><TeacherShortcutsCard /></Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
