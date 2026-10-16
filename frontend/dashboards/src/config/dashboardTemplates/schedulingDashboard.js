// Scheduling operational figures must come from verified, school-scoped APIs.
// This template provides navigation and honest empty states only. It must not
// invent attendance, enrollment, staffing, room, report, or conflict results.
export default {
  key: 'scheduling',
  activePath: '/scheduling-dashboard',
  user: { initials: 'SC', name: 'Scheduling Office', role: 'Master Schedule and Sections' },
  eyebrow: 'CROWN Scheduling',
  title: 'Scheduling',
  subtitle: 'Master schedule and section management',
  dataState: 'unavailable',
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/scheduling/summary/',
  liveDataKey: 'scheduling',
  sourceLabel: 'School-scoped scheduling metrics require verified live records.',
  note: 'No scheduling figures, events, staffing decisions or reports are assumed when live data is unavailable.',
  metrics: [],
  priorities: [],
  alerts: [],
  commandModules: [],
  trendPanels: [],
  activities: [],
  statuses: [
    { label: 'Scheduling statistics', state: 'Awaiting verified live data' },
  ],
  quickActions: [
    { label: 'View Scheduling', href: '/scheduling-dashboard' },
    { label: 'View Teacher Workloads', href: '/hr-dashboard' },
    { label: 'View Rooms', href: '/facilities-dashboard' },
  ],
};
