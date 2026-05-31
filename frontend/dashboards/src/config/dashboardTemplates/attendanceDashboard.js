import { BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'attendance',
  activePath: '/attendance',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Attendance Overview',
  subtitle: 'Daily attendance completion and intervention tracking',
  dataState: 'fallback',
  sourceLabel: 'Attendance metrics are currently dashboard-template fallbacks pending live service wiring.',
  note: 'Dashboard certification remains in review until attendance widgets are bound to canonical runtime services.',
  metrics: [
    { label: 'Present Today', value: '1,201', detail: '94 students marked absent or tardy.', accent: 'blue' },
    { label: 'Homerooms Posted', value: '100%', detail: 'All divisions reported before 8:30 AM.', accent: 'emerald' },
    { label: 'Intervention Flags', value: '7', detail: 'Counseling follow-up required.', accent: 'gold' },
    { label: 'Chronic Cases', value: '18', detail: 'Monitoring against attendance threshold.', accent: 'navy' },
  ],
  insight: { kicker: 'Attendance Trend', title: 'Campus attendance remains strong', chip: 'Morning sync complete', trend: BASE_TREND },
  activityTitle: 'Recent attendance activity',
  activities: [
    'Homeroom attendance synchronized for all grades.',
    'Attendance exception queue triaged before first bell.',
    'Counselor notifications issued for intervention cases.',
    'Daily attendance report exported for leadership.',
  ],
  quickActions: [
    { title: 'Open interventions', description: 'Review flagged student attendance patterns.', actionLabel: 'Open Interventions', href: '/attendance' },
    { title: 'Export attendance report', description: 'Generate today’s attendance snapshot.', actionLabel: 'Export Report', href: '/integrity' },
  ],
  statusTitle: 'Attendance service status',
  statuses: BASE_STATUS,
  moduleSection: {
    kicker: 'Module Focus',
    title: 'Address intervention flags before noon',
    body: 'Attendance route follows the same canonical CROWN shell to avoid design drift.',
    actions: [{ label: 'Review Queue', href: '/attendance' }, { label: 'Export Snapshot', tone: 'secondary', href: '/integrity' }],
  },
};
