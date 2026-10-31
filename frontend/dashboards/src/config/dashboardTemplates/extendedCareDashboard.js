const DATA_UNAVAILABLE = 'Not available';
const DETAILS = 'Requires independently verified school-scoped AM/PM attendance, staffing or ledger records.';

export default {
  key: 'extendedCare',
  activePath: '/extended-care-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: null,
  user: {
    initials: 'EC',
    name: 'Extended Care Program',
    role: 'Student Services - Before & After School Care',
  },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Extended Care!',
  subtitle: 'Heritage Christian Academy',
  note: 'Before/After Care KPIs, charges and safety notices are not certified. Sample summaries are excluded from operational decisions.',
  dataState: 'unavailable',
  sourceLabel: 'No verified school-scoped Extended Care metrics are available.',
  lastSyncLabel: 'No verified runtime sync',
  dataSource: 'unverified',
  requireVerifiedLiveProvenance: true,
  apiEndpoint: '/api/v1/dashboards/extended-care/summary',
  liveDataKey: 'extendedCare',
  metrics: [
    { label: 'Enrolled Students', value: DATA_UNAVAILABLE, detail: DETAILS, accent: 'blue' },
    { label: 'Attendance Today', value: DATA_UNAVAILABLE, detail: DETAILS, accent: 'emerald' },
    { label: 'Invoices Due', value: DATA_UNAVAILABLE, detail: DETAILS, accent: 'gold' },
    { label: 'Staff Coverage', value: DATA_UNAVAILABLE, detail: DETAILS, accent: 'navy' },
  ],
  insight: { kicker: 'Data verification', title: 'Care enrollment trend', chip: DATA_UNAVAILABLE, trend: [] },
  priorities: [],
  alerts: [],
  commandModules: [],
  trendPanels: [],
  activities: [],
  quickActions: [],
  statuses: [{ label: 'Operational source', state: DATA_UNAVAILABLE }],
};
