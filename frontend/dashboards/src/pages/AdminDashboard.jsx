import { useEffect, useState } from 'react';
import CrownLayout from '../components/crown/CrownLayout.jsx';
import { CrownGrid, Col } from '../components/crown/CrownGrid.jsx';
import DashboardSection from '../components/layout/DashboardSection.jsx';
import ErrorBanner from '../components/ui/ErrorBanner.jsx';

import PrayerRequests from '../components/dashboard/PrayerRequests.jsx';
import DailyDevotion from '../components/dashboard/DailyDevotion.jsx';
import SpecialDays from '../components/dashboard/SpecialDays.jsx';
import PrioritiesPanel from '../components/dashboard/PrioritiesPanel.jsx';
import AlertsPanel from '../components/dashboard/AlertsPanel.jsx';
import KpiCard from '../components/dashboard/KpiCard.jsx';
import FlipMetricCard from '../components/dashboard/FlipMetricCard.jsx';
import KpiCardGrid from '../components/dashboard/KpiCardGrid.jsx';
import ProgressGoalCard from '../components/dashboard/ProgressGoalCard.jsx';
import HealthRingCard from '../components/dashboard/HealthRingCard.jsx';
import TrendChartCard from '../components/dashboard/TrendChartCard.jsx';
import ActivityFeedCard from '../components/dashboard/ActivityFeedCard.jsx';
import OperationalSnapshotCard from '../components/dashboard/OperationalSnapshotCard.jsx';
import CalendarCard from '../components/dashboard/CalendarCard.jsx';
import CommunicationsCard from '../components/dashboard/CommunicationsCard.jsx';
import ReportSnapshotCard from '../components/dashboard/ReportSnapshotCard.jsx';

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}

function getSession() {
  try {
    return {
      token: sessionStorage.getItem('crown.jwt.access') || '',
      schoolId: sessionStorage.getItem('crown.school.id') || '',
    };
  } catch {
    return { token: '', schoolId: '' };
  }
}

async function fetchAdminMetrics() {
  const { token, schoolId } = getSession();
  const url = `${apiBase()}/api/v1/admin/metrics/`;
  const headers = { Accept: 'application/json' };

  if (token) headers.Authorization = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id'] = schoolId;

  try {
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`${res.status}`);
    return { ok: true, data: await res.json() };
  } catch {
    return { ok: false, data: null };
  }
}

function mapAlerts(data) {
  const alerts = data?.operational_alerts || [];
  if (!alerts.length) return [];

  return alerts.map((a) => ({
    label: a.label,
    detail: `${a.count} flagged item${a.count === 1 ? '' : 's'}`,
    tone: a.count > 3 ? 'red' : 'amber',
  }));
}

export default function AdminDashboard() {
  const [state, setState] = useState({ loading: true, live: false, data: null });
  const [metricsError, setMetricsError] = useState('');

  useEffect(() => {
    fetchAdminMetrics().then(({ ok, data }) => {
      if (!ok || !data) setMetricsError('Admin metrics unavailable - API error');
      setState({ loading: false, live: ok && !!data, data });
    });
  }, []);

  const { loading, data } = state;

  const enrollmentValue = loading
    ? '...'
    : String(data?.enrolled ?? 412);

  const attendanceValue = loading
    ? '...'
    : data?.attendance_rate
    ? `${Math.round(data.attendance_rate)}%`
    : '91%';

  const alerts = mapAlerts(data);

  return (
    <CrownLayout
      title="Executive Portal"
      subtitle="Faith, leadership, and school operations command center"
    >
      <h1 className="text-2xl font-semibold tracking-tight">Administration</h1>
      <h2 className="text-sm font-medium uppercase tracking-wide">Executive Dashboard</h2>

      <ErrorBanner title="Dashboard unavailable" message={metricsError} />

      <DashboardSection title="Faith and Community">
        <CrownGrid>
          <Col span={3}>
            <PrayerRequests />
          </Col>

          <Col span={6}>
            <DailyDevotion />
          </Col>

          <Col span={3}>
            <SpecialDays />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Leadership Action">
        <CrownGrid>
          <Col span={3}>
            <PrioritiesPanel />
          </Col>

          <Col span={6}>
            <KpiCardGrid>
              <KpiCard
                title="Enrolled"
                value={enrollmentValue}
                trend="+4% vs last year"
                icon="ENR"
                tone="good"
              />

              <KpiCard
                title="Attendance Flags"
                value={attendanceValue}
                trend="Stable this week"
                icon="ATT"
                tone="good"
              />

              <FlipMetricCard
                title="Discipline"
                value="2"
                trend="Incidents this week"
                definition="Weekly discipline incident count requiring administrative follow-up."
                sources={[
                  'Discipline Log',
                  'Behavior Referrals',
                  'Dean Notes',
                ]}
                links={[
                  'Open Discipline Dashboard',
                  'View Incident List',
                  'Export Weekly Summary',
                ]}
              />

              <FlipMetricCard
                title="Messages Pending"
                value="8"
                trend="Awaiting response"
                definition="Messages requiring action from school leadership queues."
                sources={[
                  'Communications Inbox',
                  'Family Support Queue',
                  'Operations Notifications',
                ]}
                links={[
                  'Open Communications',
                  'View Priority Threads',
                  'Export Queue',
                ]}
              />
            </KpiCardGrid>
          </Col>

          <Col span={3}>
            <AlertsPanel alerts={alerts} />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Executive Insights">
        <CrownGrid>
          <Col span={4}>
            <ProgressGoalCard
              title="Receivables"
              current={412}
              goal={450}
              percentLabel="91%"
              detail="412 of 450 students enrolled"
              colorClass="var(--crown-brand)"
            />
          </Col>

          <Col span={4}>
            <ProgressGoalCard
              title="Aid Allocated"
              current={2340}
              goal={3000}
              percentLabel="78%"
              detail="2,340 of 3,000 annual service hours"
              colorClass="#059669"
            />
          </Col>

          <Col span={4}>
            <HealthRingCard
              title="Academic Risk"
              percent={88}
              subtitle="Composite score"
              detail="Overdue Work remains concentrated in grades 9-10 and needs intervention."
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Enrollment Funnel">
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
              title="Attendance Trend by Grade"
              subtitle="Average attendance rate this month"
              labels={['Grade 1', 'Grade 3', 'Grade 5', 'Grade 7', 'Grade 9', 'Grade 11']}
              datasets={[
                {
                  label: 'Attendance %',
                  data: [95, 94, 92, 91, 88, 90],
                  borderColor: '#004687',
                },
              ]}
              type="bar"
            />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Operational Detail">
        <CrownGrid>
          <Col span={4}>
            <ActivityFeedCard />
          </Col>

          <Col span={8}>
            <OperationalSnapshotCard />
          </Col>
        </CrownGrid>
      </DashboardSection>

      <DashboardSection title="Awareness, Communication, and Reporting">
        <CrownGrid>
          <Col span={4}>
            <CalendarCard />
          </Col>

          <Col span={4}>
            <CommunicationsCard />
          </Col>

          <Col span={4}>
            <ReportSnapshotCard />
          </Col>
        </CrownGrid>
      </DashboardSection>
    </CrownLayout>
  );
}
