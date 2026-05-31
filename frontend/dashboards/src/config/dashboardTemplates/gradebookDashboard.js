import { BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'gradebook',
  activePath: '/gradebook',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Academic Performance View',
  subtitle: 'Grading progress, missing work, and at-risk tracking',
  dataState: 'fallback',
  sourceLabel: 'Gradebook widgets currently use template snapshots pending live gradebook service integration.',
  note: 'Certification remains in review until gradebook metrics are sourced from canonical runtime endpoints.',
  metrics: [
    { label: 'Assignments Graded', value: '482', detail: '92% completion rate this week.', accent: 'blue' },
    { label: 'Missing Work', value: '39', detail: 'Down 11% since Monday.', accent: 'gold' },
    { label: 'At-Risk Students', value: '18', detail: 'Counselor review scheduled.', accent: 'navy' },
    { label: 'Grade Sync', value: '99%', detail: 'Last synchronization completed.', accent: 'emerald' },
  ],
  insight: { kicker: 'Gradebook Trend', title: 'Assignment completion is improving', chip: 'Updated by faculty', trend: BASE_TREND },
  activityTitle: 'Recent gradebook activity',
  activities: [
    'Science section grades posted after lab review.',
    'Late assignment reminders sent to students.',
    'Category weight adjustments queued for approval.',
    'At-risk summary shared with counseling team.',
  ],
  quickActions: [
    { title: 'Open grading queue', description: 'Prioritize ungraded assignments by course.', actionLabel: 'Open Queue', href: '/gradebook' },
    { title: 'Review at-risk list', description: 'Inspect students below performance threshold.', actionLabel: 'Open Alerts', href: '/student-services' },
  ],
  statusTitle: 'Gradebook service status',
  statuses: BASE_STATUS,
  moduleSection: {
    kicker: 'Module Focus',
    title: 'Reduce missing work and finalize weekly grades',
    body: 'Gradebook now renders through the same CROWN template system used by School Administrator.',
    actions: [{ label: 'Review Queue', href: '/gradebook' }, { label: 'Export Snapshot', tone: 'secondary', href: '/integrity' }],
  },
};
