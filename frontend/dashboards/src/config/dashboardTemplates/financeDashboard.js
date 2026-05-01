import { BASE_NOTE, BASE_STATUS, BASE_TREND } from './_baseData.js';

export default {
  key: 'finance',
  activePath: '/finance',
  schoolName: 'Heritage Christian Academy',
  eyebrow: 'CROWN Launch Preview',
  title: 'Finance Overview',
  subtitle: 'Receivables, deposits, and payment-plan health',
  note: BASE_NOTE,
  metrics: [
    { label: 'Receivables', value: '$148K', detail: 'Current family balances outstanding.', accent: 'blue' },
    { label: 'Deposits Posted', value: '$82K', detail: 'Today’s batch completed successfully.', accent: 'emerald' },
    { label: 'Payment Plans', value: '412', detail: '98% active without issue.', accent: 'gold' },
    { label: 'Exceptions Queue', value: '9', detail: 'Requires finance specialist review.', accent: 'navy' },
  ],
  insight: { kicker: 'Finance Trend', title: 'Collections remain on target', chip: 'Ledger sync healthy', trend: BASE_TREND },
  activityTitle: 'Recent finance activity',
  activities: [
    'Compuwerx payout batch reconciled successfully.',
    'Family statement exports completed for leadership.',
    'Payment exceptions triaged for specialist review.',
    'Dispute workbench queue updated after bank sync.',
  ],
  quickActions: [
    { title: 'Open receivables', description: 'Review overdue balances by family account.', actionLabel: 'Open Receivables' },
    { title: 'Review exceptions', description: 'Triage finance exception queue.', actionLabel: 'Open Exceptions' },
  ],
  statusTitle: 'Finance service status',
  statuses: BASE_STATUS,
  moduleSection: {
    kicker: 'Module Focus',
    title: 'Close exceptions and maintain payout cadence',
    body: 'Finance route now inherits the canonical CROWN dashboard composition to eliminate visual drift.',
    actions: [{ label: 'Review Queue' }, { label: 'Export Snapshot', tone: 'secondary' }],
  },
};
