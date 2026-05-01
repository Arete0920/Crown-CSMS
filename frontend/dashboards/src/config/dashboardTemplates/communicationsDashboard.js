import { BASE_NOTE, BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'communications',
  activePath: '/communications',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Communications Hub',
  subtitle: 'Message queue, unread threads, and announcements',
  note: BASE_NOTE,
  metrics: [
    { label: 'Queued Messages', value: '18', detail: 'Family update ready for approval.', accent: 'blue' },
    { label: 'Unread Threads', value: '9', detail: 'Front office triage before lunch.', accent: 'gold' },
    { label: 'Announcements Sent', value: '4', detail: 'This morning across all divisions.', accent: 'royal' },
    { label: 'Delivery Health', value: '99.4%', detail: 'Outbound communications success rate.', accent: 'emerald' },
  ],
  insight: { kicker: 'Comms Trend', title: 'Engagement is consistent across channels', chip: 'Delivery healthy', trend: BASE_TREND },
  activityTitle: 'Recent communications activity',
  activities: [
    'Weekly parent bulletin queued for publication.',
    'Unread thread triage assigned to front office.',
    'Athletics event reminder sent to families.',
    'Open-response metrics updated in dashboard.',
  ],
  quickActions: [
    { title: 'Publish update', description: 'Release pending family communications.', actionLabel: 'Publish' },
    { title: 'Open thread triage', description: 'Resolve high-priority unread conversations.', actionLabel: 'Open Triage' },
  ],
  statusTitle: 'Communications service status',
  statuses: BASE_STATUS,
  moduleSection: {
    kicker: 'Module Focus',
    title: 'Maintain response quality and publication cadence',
    body: 'Communications uses the same CROWN template primitives as all core dashboards.',
    actions: [{ label: 'Review Queue' }, { label: 'Export Snapshot', tone: 'secondary' }],
  },
};
