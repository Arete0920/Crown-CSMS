import { BASE_NOTE } from './_baseData.js';

const CIRC_TREND = [
  { month: 'Aug', value: 124 }, { month: 'Sep', value: 218 }, { month: 'Oct', value: 264 },
  { month: 'Nov', value: 241 }, { month: 'Dec', value: 196 }, { month: 'Jan', value: 228 },
  { month: 'Feb', value: 252 }, { month: 'Mar', value: 274 },
];
const OVERDUE_TREND = [
  { month: 'Aug', value: 4 }, { month: 'Sep', value: 8 }, { month: 'Oct', value: 12 },
  { month: 'Nov', value: 9 }, { month: 'Dec', value: 6 }, { month: 'Jan', value: 11 },
  { month: 'Feb', value: 8 }, { month: 'Mar', value: 7 },
];

export default {
  key: 'libraryMedia',
  activePath: '/library-media-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'LM', name: 'Library & Media Center', role: 'Academics â€” Library & Media Services' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Library!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Library and media widgets currently use template snapshots pending live service integration.',
  note: 'Certification remains in review until library and media metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/libraryMedia/summary/',
  liveDataKey: 'libraryMedia',
  metrics: [
    { label: 'Books Circulating', value: '274', detail: 'March all-time high â€” 44% of collection active.', accent: 'blue' },
    { label: 'Overdue Items', value: '7', detail: '3 past 14-day notice â€” families contacted.', accent: 'gold' },
    { label: 'Digital Resources', value: '18', detail: '18 active databases and e-resource subscriptions.', accent: 'emerald' },
    { label: 'Research Requests', value: '12', detail: 'This week â€” 8 class projects, 4 individual.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Process 3 long-overdue returns', detail: '14+ day notice sent â€” 2 families have not responded.', state: 'Today', tone: 'warn' },
    { title: 'Set up 5th grade research project', detail: 'Class visit Friday â€” research guide and databases ready.', state: 'This week', tone: 'nominal' },
    { title: 'Renew ProQuest subscription', detail: 'Renewal invoice due April 30 â€” approval needed.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Library priorities',

  alerts: [
    { title: '2 families unresponsive to overdue notices', detail: 'Items 21+ days overdue â€” escalate to office.', tone: 'warn' },
    { title: 'ProQuest subscription renewal due April 30', detail: '$1,240 annual renewal â€” needs finance approval.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'circulation', icon: 'CI', title: 'Circulation', status: 'Active', statusTone: 'good',
      mainKpi: '274 items out â€” March record', summary: 'Circulation at all-time monthly high â€” healthy engagement.',
      kpis: [{ label: 'Checked Out', value: '274' }, { label: 'Collection Size', value: '6,200' }, { label: 'Utilization', value: '44%' }, { label: 'Due Today', value: '18' }],
      details: ['274 items currently checked out', '6,200 total items in collection', '18 items due back today', 'Hold queue: 9 items waiting'],
      primaryActionLabel: 'Circulation Desk', backActionLabel: 'Catalog',
      primaryActionHref: '/library-media-dashboard', backActionHref: '/library-media-dashboard', lastUpdated: '8:00 AM' },
    { key: 'overdue', icon: 'OV', title: 'Overdue Items', status: 'Watch', statusTone: 'warn',
      mainKpi: '7 overdue â€” 2 families unresponsive', summary: 'Escalation needed for 2 families at 21+ days.',
      kpis: [{ label: 'Overdue', value: '7' }, { label: '1st Notice', value: '4' }, { label: '2nd Notice', value: '3' }, { label: 'Unresponsive', value: '2' }],
      details: ['7 items overdue total', '3 past second notice â€” escalation pending', '2 families have not responded to notices', 'Replacement cost policy: $20 minimum'],
      primaryActionLabel: 'Overdue Report', backActionLabel: 'Student Records',
      primaryActionHref: '/library-media-dashboard', backActionHref: '/library-media-dashboard', lastUpdated: '8:05 AM' },
    { key: 'digital', icon: 'DG', title: 'Digital Resources', status: 'Stable', statusTone: 'good',
      mainKpi: '18 active subscriptions', summary: 'All databases current â€” ProQuest renewal due April 30.',
      kpis: [{ label: 'Active', value: '18' }, { label: 'Renewal Due', value: '1' }, { label: 'Budget', value: '$4,200' }, { label: 'Usage This Month', value: '412' }],
      details: ['18 database and e-resource subscriptions', 'ProQuest renewal due April 30 ($1,240)', 'Digital resource usage: 412 sessions this month', 'EBSCO, Gale, ProQuest, BrainPOP all active'],
      primaryActionLabel: 'Digital Resources', backActionLabel: 'Renewal Schedule',
      primaryActionHref: '/library-media-dashboard', backActionHref: '/library-media-dashboard', lastUpdated: '8:10 AM' },
    { key: 'research', icon: 'RS', title: 'Research Support', status: 'Active', statusTone: 'good',
      mainKpi: '12 research requests this week', summary: '8 class projects, 4 individual â€” all being supported.',
      kpis: [{ label: 'Requests', value: '12' }, { label: 'Class Projects', value: '8' }, { label: 'Individual', value: '4' }, { label: 'Classes Visiting', value: '3' }],
      details: ['8 class research projects ongoing', '4 individual student research requests', '5th grade class visit Friday â€” prep needed', 'Research guides published for 4 units'],
      primaryActionLabel: 'Research Hub', backActionLabel: 'Class Schedule',
      primaryActionHref: '/library-media-dashboard', backActionHref: '/scheduling-dashboard', lastUpdated: '8:15 AM' },
    { key: 'collection', icon: 'CN', title: 'Collection Development', status: 'Stable', statusTone: 'good',
      mainKpi: '6,200 items â€” 24 new acquisitions', summary: 'Spring acquisition order approved â€” items arriving May.',
      kpis: [{ label: 'Collection Size', value: '6,200' }, { label: 'New YTD', value: '84' }, { label: 'On Order', value: '24' }, { label: 'Deaccessioned', value: '12' }],
      details: ['84 new items added this academic year', '24 items on order â€” arriving May 10', '12 outdated items deaccessioned', 'Curriculum alignment review Q4'],
      primaryActionLabel: 'Catalog', backActionLabel: 'Order Status',
      primaryActionHref: '/library-media-dashboard', backActionHref: '/library-media-dashboard', lastUpdated: '8:20 AM' },
    { key: 'media', icon: 'MD', title: 'Media Services', status: 'Stable', statusTone: 'good',
      mainKpi: '6 AV requests this week', summary: 'Projectors, document cameras, and streaming all operational.',
      kpis: [{ label: 'AV Requests', value: '6' }, { label: 'Equipment Out', value: '4' }, { label: 'Issues', value: '0' }, { label: 'Streaming Active', value: '2' }],
      details: ['6 AV equipment requests processed', '4 items currently checked out to classrooms', 'All AV equipment operational', 'Streaming setup for 2 events this week'],
      primaryActionLabel: 'AV Requests', backActionLabel: 'Media Inventory',
      primaryActionHref: '/library-media-dashboard', backActionHref: '/library-media-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Book circulation', title: 'Items Checked Out Per Month', chip: '274 â€” March record', trend: CIRC_TREND },
    { kicker: 'Overdue tracking', title: 'Overdue Items Per Month', chip: '7 current', trend: OVERDUE_TREND },
  ],

  activities: [
    '2 unresponsive families escalated to school office for overdue items.',
    'ProQuest renewal invoice routed to finance for approval.',
    '5th grade research visit setup for Friday â€” guides ready.',
    '24 new books on order â€” expected May 10.',
    '274 items checked out â€” March monthly record set.',
  ],

  quickActions: [
    { label: 'Circulation Desk', href: '/library-media-dashboard' },
    { label: 'Overdue Report', href: '/library-media-dashboard' },
    { label: 'Digital Resources', href: '/library-media-dashboard' },
    { label: 'Research Hub', href: '/library-media-dashboard' },
  ],

  statuses: [
    { label: 'Circulation', state: '274 out (record)' },
    { label: 'Overdue Items', state: '7 (2 escalated)' },
    { label: 'Digital Resources', state: '18 active' },
    { label: 'ProQuest Renewal', state: 'Due April 30' },
  ],
};

