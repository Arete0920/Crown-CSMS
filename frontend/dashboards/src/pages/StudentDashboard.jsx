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

import StudentAtAGlanceCard from '../components/dashboard/student/StudentAtAGlanceCard.jsx';
import StudentPrioritiesPanel from '../components/dashboard/student/StudentPrioritiesPanel.jsx';
import StudentAlertsPanel from '../components/dashboard/student/StudentAlertsPanel.jsx';
import StudentActivityFeedCard from '../components/dashboard/student/StudentActivityFeedCard.jsx';
import StudentCourseSnapshotCard from '../components/dashboard/student/StudentCourseSnapshotCard.jsx';
import StudentScheduleCard from '../components/dashboard/student/StudentScheduleCard.jsx';
import StudentMessagesCard from '../components/dashboard/student/StudentMessagesCard.jsx';
import StudentShortcutsCard from '../components/dashboard/student/StudentShortcutsCard.jsx';

export default function StudentDashboard() {
  return (
    <CrownLayout
      title="Student Dashboard"
      subtitle="Assignments, grades, attendance, schedule, and daily student progress"
    >
      <h1 className="text-2xl font-semibold tracking-tight">Student Dashboard</h1>

      <DashboardSection title="Daily Mission and Student Snapshot">
        <CrownGrid>
          <Col span={6}><DailyDevotion /></Col>
          <Col span={3}><SpecialDays /></Col>
          <Col span={3}><StudentAtAGlanceCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Student Action">
        <CrownGrid>
          <Col span={3}><StudentPrioritiesPanel /></Col>

          <Col span={6}>
            <KpiCardGrid>
              <KpiCard title="My GPA" value="3.5" trend="Strong this term" icon="GR" tone="good" />
              <KpiCard title="Current Average" value="91.2%" trend="+2 this week" icon="AVG" tone="good" />
              <KpiCard title="Missing Work" value="1" trend="Needs submission" icon="MSW" tone="warn" />
              <KpiCard title="Balance Due" value="$250" trend="Current student account" icon="BIL" tone="warn" />
            </KpiCardGrid>
          </Col>

          <Col span={3}><StudentAlertsPanel /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Student Progress">
        <CrownGrid>
          <Col span={4}>
            <ProgressGoalCard
              title="Service Hours"
              current={12}
              goal={20}
              percentLabel="60%"
              detail="Approved hours logged this term"
              colorClass="var(--crown-brand)"
            />
          </Col>

          <Col span={4}>
            <ProgressGoalCard
              title="Attendance Progress"
              current={97}
              goal={100}
              percentLabel="97%"
              detail="Attendance rate for the current term"
              colorClass="#059669"
            />
          </Col>

          <Col span={4}>
            <HealthRingCard
              title="Student Progress Index"
              percent={88}
              subtitle="Overall student status"
              detail="Grades and attendance are healthy overall. A few missing assignments need attention."
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Upcoming Assignments">
        <CrownGrid>
          <Col span={6}>
            <TrendChartCard
              title="Assignment Completion Trend"
              subtitle="Recent completion pattern"
              labels={['Week 1', 'Week 2', 'Week 3', 'Week 4']}
              datasets={[
                {
                  label: 'Completion %',
                  data: [82, 86, 84, 88],
                  borderColor: '#004687',
                },
              ]}
            />
          </Col>

          <Col span={6}>
            <TrendChartCard
              title="Grade Trend"
              subtitle="Average grade movement"
              labels={['Week 1', 'Week 2', 'Week 3', 'Week 4']}
              datasets={[
                {
                  label: 'Average Grade',
                  data: [86, 87, 88, 89],
                  borderColor: '#004687',
                },
              ]}
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Recent Academic Detail">
        <CrownGrid>
          <Col span={4}><StudentActivityFeedCard /></Col>
          <Col span={8}><StudentCourseSnapshotCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Schedule, Messages, and Shortcuts">
        <CrownGrid>
          <Col span={4}><StudentScheduleCard /></Col>
          <Col span={4}><StudentMessagesCard /></Col>
          <Col span={4}><StudentShortcutsCard /></Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Quick Links">
        <CrownGrid>
          <Col span={12}><a href="/gradebook">Open Gradebook</a></Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
