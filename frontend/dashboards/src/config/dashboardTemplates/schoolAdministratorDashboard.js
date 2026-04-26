import { BASE_ACTIVITY, BASE_NOTE, BASE_OPERATIONS, BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'schoolAdministrator',
  activePath: '/school-admin',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Sarah!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  metrics: [
    { label: 'Total Students', value: '1,248', detail: 'Enrollment is up 4.1% from last semester.', accent: 'blue' },
    { label: 'Faculty & Staff', value: '156', detail: 'Three new hires completed onboarding this week.', accent: 'navy' },
    { label: 'Attendance Rate', value: '96.2%', detail: 'Steady above benchmark across all divisions.', accent: 'gold' },
    { label: 'Tuition Collected', value: '$2.4M', detail: '94% of semester target collected to date.', accent: 'emerald' },
  ],
  insight: {
    kicker: 'Enrollment Trend',
    title: 'Steady growth across the school year',
    chip: 'Updated this morning',
    trend: BASE_TREND,
  },
  activityTitle: 'Launch-ready operational rhythm',
  activities: BASE_ACTIVITY,
  quickActions: [
    {
      title: 'Send family update',
      description: 'Publish the weekly school update with attendance, events, and key reminders.',
      actionLabel: 'Prepare Update',
      allowedRoles: ['schoolAdministrator'],
    },
    {
      title: 'Review enrollment pipeline',
      description: 'Jump into admissions priorities and accepted-student follow-up for next week.',
      actionLabel: 'Open Pipeline',
      allowedRoles: ['schoolAdministrator'],
    },
  ],
  statusTitle: 'Core systems are stable',
  statuses: BASE_STATUS,
  operationsTitle: 'Today’s cross-team readiness snapshot',
  operations: BASE_OPERATIONS,
};
