const DATA_UNAVAILABLE = 'Not available';
const DETAILS = 'Requires verified school-scoped operational records; the summary endpoint currently serves sample data.';

export default {
  key: 'summerCamp',
  activePath: '/summer-camp-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: null,
  user: {
    initials: 'SC',
    name: 'Summer Camp Operations',
    role: 'Seasonal Program Director',
  },
  eyebrow: 'CROWN Launch Preview',
  title: 'Summer program command center',
  subtitle: 'Heritage Christian Academy',
  note: 'Camp KPIs and trends are not certified. Sample summaries are excluded; use authenticated Camp records for operational decisions.',
  dataState: 'unavailable',
  sourceLabel: 'No verified school-scoped Summer Camp metrics are available.',
  lastSyncLabel: 'No verified runtime sync',
  dataSource: 'unverified',
  requireVerifiedLiveProvenance: true,
  apiEndpoint: '/api/v1/dashboards/summer-camp/summary',
  liveDataKey: 'summerCamp',
  metrics: [
    { label: 'Registered Campers', value: DATA_UNAVAILABLE, detail: DETAILS, accent: 'blue' },
    { label: 'Staffed Sessions', value: DATA_UNAVAILABLE, detail: DETAILS, accent: 'emerald' },
    { label: 'Waitlist Families', value: DATA_UNAVAILABLE, detail: DETAILS, accent: 'gold' },
    { label: 'Transport Confirmed', value: DATA_UNAVAILABLE, detail: DETAILS, accent: 'navy' },
  ],
  insight: { kicker: 'Data verification', title: 'Camp registration trend', chip: DATA_UNAVAILABLE, trend: [] },
  priorities: [],
  alerts: [],
  commandModules: [],
  trendPanels: [],
  activities: [],
  quickActions: [],
  statuses: [{ label: 'Operational source', state: DATA_UNAVAILABLE }],
};
