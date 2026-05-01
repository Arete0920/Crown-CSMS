import { BASE_NOTE, BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'admissions',
  activePath: '/admissions',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Admissions Command Center',
  subtitle: 'Pipeline, accepted students, and family follow-up',
  note: BASE_NOTE,
  metrics: [
    { label: 'Open Applications', value: '84', detail: '12 awaiting family follow-up.', accent: 'blue' },
    { label: 'Accepted Students', value: '31', detail: '6 families ready to enroll.', accent: 'gold' },
    { label: 'Tours Scheduled', value: '14', detail: 'Three new families booked today.', accent: 'navy' },
    { label: 'Conversion Rate', value: '68%', detail: 'Current cycle conversion trend.', accent: 'emerald' },
  ],
  insight: { kicker: 'Admissions Trend', title: 'Pipeline velocity remains healthy', chip: 'Updated today', trend: BASE_TREND },
  activityTitle: 'Recent admissions activity',
  activities: [
    'Tour confirmations sent to new families.',
    'Application documents validated for intake.',
    'Enrollment interview notes finalized.',
    'Welcome communications queued for accepted students.',
  ],
  quickActions: [
    { title: 'Review pipeline', description: 'Focus on applicants needing immediate contact.', actionLabel: 'Open Pipeline' },
    { title: 'Send acceptance follow-up', description: 'Contact families with pending confirmations.', actionLabel: 'Send Follow-up' },
  ],
  statusTitle: 'Admissions systems stable',
  statuses: BASE_STATUS,
  moduleSection: {
    kicker: 'Module Focus',
    title: 'Prioritize accepted-student conversion this week',
    body: 'This module uses the same CROWN dashboard template as School Administrator for visual consistency.',
    actions: [{ label: 'Review Queue' }, { label: 'Export Snapshot', tone: 'secondary' }],
  },
};
