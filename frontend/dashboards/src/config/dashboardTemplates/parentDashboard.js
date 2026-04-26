import { BASE_NOTE, BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'parent',
  activePath: '/parent',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Parent Dashboard',
  subtitle: 'Family academics, attendance, billing, and school communications',
  note: BASE_NOTE,
  metrics: [
    { label: 'Children Enrolled', value: '2', detail: 'Both learners active in current term.', accent: 'blue' },
    { label: 'Missing Assignments', value: '7', detail: 'Across all enrolled students.', accent: 'gold' },
    { label: 'Household Balance', value: '$620', detail: 'Current family account balance.', accent: 'navy' },
    { label: 'Upcoming', value: '5', detail: 'Events and due dates this week.', accent: 'emerald' },
  ],
  insight: {
    kicker: 'Family Trend',
    title: 'Attendance and academic performance remain strong',
    chip: 'Parent overview',
    trend: BASE_TREND,
  },
  activityTitle: 'Recent family activity',
  activities: [
    'Math assignment submitted before deadline.',
    'Field trip consent form approved.',
    'Weekly parent bulletin opened.',
    'Attendance summary reviewed for both students.',
  ],
  quickActions: [
    { title: 'View gradebook', description: 'Open grade summary and assignment details.', actionLabel: 'Open Gradebook', allowedRoles: ['parent'] },
    { title: 'Review family billing', description: 'Check invoices and payment options.', actionLabel: 'Open Billing', allowedRoles: ['parent'] },
  ],
  statusTitle: 'Family service status',
  statuses: BASE_STATUS,
  moduleSection: {
    kicker: 'Family Focus',
    title: 'Keep assignments and billing on track',
    body: 'Shared CROWN shell is preserved while parent-facing data and actions are tailored.',
    actions: [
      { label: 'View Student Snapshot', href: '/academics/parent-snapshot' },
      { label: 'Open Billing', href: '/finance/invoices', tone: 'secondary' },
    ],
  },
};
