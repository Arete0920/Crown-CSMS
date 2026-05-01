import { BASE_NOTE, BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'student',
  activePath: '/student',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Student Dashboard',
  subtitle: 'Assignments, grades, attendance, schedule, and daily progress',
  note: BASE_NOTE,
  metrics: [
    { label: 'Current Average', value: '91.2%', detail: 'Up 2 points this week.', accent: 'blue' },
    { label: 'Missing Work', value: '1', detail: 'Needs submission today.', accent: 'gold' },
    { label: 'Balance Due', value: '$250', detail: 'Current student account balance.', accent: 'royal' },
    { label: 'My GPA', value: '3.4', detail: 'Estimated cumulative performance.', accent: 'emerald' },
  ],
  insight: {
    kicker: 'Academic Trend',
    title: 'Performance remains stable across core classes',
    chip: 'Student momentum',
    trend: BASE_TREND,
  },
  activityTitle: 'Upcoming Assignments',
  activities: [
    'Service Hours progress updated for this week.',
    'English reflection assignment submitted.',
    'Biology quiz score posted.',
    'Advisory attendance marked present.',
    'New announcement read in communications.',
  ],
  quickActions: [
    { title: 'Open assignments', description: 'Review tasks due this week.', actionLabel: 'View Assignments', allowedRoles: ['student'] },
    { title: 'Open attendance', description: 'Check attendance and tardy history.', actionLabel: 'View Attendance', allowedRoles: ['student'] },
  ],
  statusTitle: 'Student system status',
  statuses: BASE_STATUS,
  moduleSection: {
    kicker: 'Learning Focus',
    title: 'Complete remaining work and prepare for assessments',
    body: 'Shared CROWN visual framework remains consistent while student content is personalized.',
    actions: [{ label: 'Gradebook', href: '/gradebook' }, { label: 'Review Schedule', tone: 'secondary' }],
  },
};
