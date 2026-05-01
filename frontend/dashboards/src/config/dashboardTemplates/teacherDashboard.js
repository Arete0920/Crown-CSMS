import { BASE_NOTE, BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'teacher',
  activePath: '/teacher',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Teacher Dashboard',
  subtitle: 'Classroom execution, attendance, grading, and communication',
  note: BASE_NOTE,
  metrics: [
    { label: 'Classes Today', value: '5', detail: 'Full teaching schedule active.', accent: 'blue' },
    { label: 'Attendance Posted', value: '4/5', detail: 'One class remaining.', accent: 'gold' },
    { label: 'Assignments to Grade', value: '23', detail: 'Needs end-of-day completion.', accent: 'royal' },
    { label: 'Parent Messages', value: '3', detail: 'Unread this morning.', accent: 'emerald' },
  ],
  insight: {
    kicker: 'Classroom Trend',
    title: 'Attendance and completion stay stable',
    chip: 'Live classroom pulse',
    trend: BASE_TREND,
  },
  activityTitle: 'Recent classroom activities',
  activities: [
    'Grade 8 attendance synced for first period.',
    'Algebra assignments submitted by 92% of class.',
    'Parent follow-up sent for two missing assignments.',
    'Weekly lesson plans published to class feed.',
  ],
  quickActions: [
    { title: 'Open grade queue', description: 'Review and post outstanding assignment grades.', actionLabel: 'Open Gradebook', allowedRoles: ['teacher'] },
    { title: 'Finalize attendance', description: 'Submit attendance for the remaining class period.', actionLabel: 'Submit Attendance', allowedRoles: ['teacher'] },
  ],
  statusTitle: 'Teacher workspace status',
  statuses: BASE_STATUS,
  moduleSection: {
    kicker: 'Teaching Focus',
    title: 'Prioritize grading and parent follow-up today',
    body: 'The shared CROWN template remains intact while teacher data and actions are role-specific.',
    actions: [{ label: 'Review Queue' }, { label: 'Open Communications', tone: 'secondary' }],
  },
};
