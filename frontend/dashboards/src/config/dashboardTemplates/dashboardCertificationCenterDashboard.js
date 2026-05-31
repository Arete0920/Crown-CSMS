import { BASE_NOTE } from './_baseData.js';

const CERT_TREND = [
  { month: 'Aug', value: 2 }, { month: 'Sep', value: 6 }, { month: 'Oct', value: 12 },
  { month: 'Nov', value: 18 }, { month: 'Dec', value: 22 }, { month: 'Jan', value: 28 },
  { month: 'Feb', value: 34 }, { month: 'Mar', value: 41 },
];
const RATE_TREND = [
  { month: 'Aug', value: 50 }, { month: 'Sep', value: 62 }, { month: 'Oct', value: 71 },
  { month: 'Nov', value: 78 }, { month: 'Dec', value: 82 }, { month: 'Jan', value: 84 },
  { month: 'Feb', value: 88 }, { month: 'Mar', value: 91 },
];

export default {
  key: 'dashboardCertificationCenter',
  activePath: '/dashboard-certification-center',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'DC', name: 'Dashboard Certification Center', role: 'Platform â€” Dashboard Quality & Certification Authority' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Certification Center!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/dashboardCertificationCenter/summary/',
  liveDataKey: 'dashboardCertificationCenter',

  metrics: [
    { label: 'Dashboards Certified', value: '41', detail: '41 of 45 submitted dashboards fully certified.', accent: 'emerald' },
    { label: 'Pending Review', value: '6', detail: '6 dashboards in review queue.', accent: 'gold' },
    { label: 'Failed Certification', value: '2', detail: '2 dashboards require corrections before re-submit.', accent: 'navy' },
    { label: 'Cert Rate', value: '91%', detail: 'First-pass certification rate â€” target 90%.', accent: 'blue' },
  ],

  priorities: [
    { title: 'Complete 6 dashboards in review queue', detail: 'All 6 in queue â€” target clearance this week.', state: 'This week', tone: 'warn' },
    { title: 'Return 2 failed dashboards with corrections', detail: 'Feedback package ready â€” send correction guidance today.', state: 'Today', tone: 'warn' },
    { title: 'Publish Q2 certification report', detail: 'Quarterly summary of all certified and pending dashboards.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Certification priorities',

  alerts: [
    { title: '6 dashboards pending review â€” target clearance this week', detail: 'Clear queue before end of sprint to stay on schedule.', tone: 'warn' },
    { title: '2 failed dashboards need correction guidance', detail: 'Send feedback packages today â€” resubmit deadline April 18.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'certified', icon: 'CT', title: 'Certified Dashboards', status: 'On Track', statusTone: 'good',
      mainKpi: '41 certified â€” 91% first-pass rate', summary: 'Above 90% target â€” steady growth in certification volume.',
      kpis: [{ label: 'Certified', value: '41' }, { label: 'Submitted', value: '45' }, { label: 'First-Pass Rate', value: '91%' }, { label: 'Target', value: '90%' }],
      details: ['41 of 45 submitted dashboards certified', '91% first-pass certification rate', 'Target 90% â€” currently exceeding', 'Gold standard: CrownDashboardTemplate compliance'],
      primaryActionLabel: 'Certified List', backActionLabel: 'Certification Log',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: '8:00 AM' },
    { key: 'review', icon: 'RV', title: 'Review Queue', status: 'Active', statusTone: 'warn',
      mainKpi: '6 dashboards in review queue', summary: 'Clear queue this week â€” all assigned to reviewers.',
      kpis: [{ label: 'In Queue', value: '6' }, { label: 'Assigned', value: '6' }, { label: 'Avg Review Time', value: '2.4 days' }, { label: 'SLA', value: '5 days' }],
      details: ['6 dashboards pending review', 'All 6 assigned to certified reviewers', 'Average review cycle: 2.4 days', 'SLA target: complete within 5 business days'],
      primaryActionLabel: 'Review Queue', backActionLabel: 'Assign Reviewers',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: '8:05 AM' },
    { key: 'failed', icon: 'FL', title: 'Failed Certification', status: 'Action Required', statusTone: 'warn',
      mainKpi: '2 failed â€” correction guidance needed today', summary: 'Resubmission deadline April 18.',
      kpis: [{ label: 'Failed', value: '2' }, { label: 'Resubmit Deadline', value: 'Apr 18' }, { label: 'Issues', value: 'Layout + Data' }, { label: 'Feedback', value: 'Ready' }],
      details: ['Dashboard A: missing commandModules â€” layout non-compliant', 'Dashboard B: incorrect data source mapping', 'Correction feedback packages prepared', 'Resubmission deadline: April 18'],
      primaryActionLabel: 'Failed Dashboards', backActionLabel: 'Send Feedback',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: '8:10 AM' },
    { key: 'standards', icon: 'SD', title: 'Standards', status: 'Current', statusTone: 'good',
      mainKpi: 'Gold standard: CrownDashboardTemplate', summary: 'All dashboards must use approved template pattern.',
      kpis: [{ label: 'Standard', value: 'CrownDashboardTemplate' }, { label: 'Version', value: 'v4.x' }, { label: 'Required Fields', value: '22' }, { label: 'Published', value: 'March 2026' }],
      details: ['Gold standard: CrownDashboardTemplate with full commandModules', '22 required config fields for certification', 'Docs published to engineering portal March 2026', 'Yearly standard review: Q4'],
      primaryActionLabel: 'Standards Docs', backActionLabel: 'Template Guide',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: '8:15 AM' },
    { key: 'training', icon: 'TR', title: 'Reviewer Training', status: 'Current', statusTone: 'good',
      mainKpi: '6 certified reviewers active', summary: 'All reviewers trained on v4 standards.',
      kpis: [{ label: 'Reviewers', value: '6' }, { label: 'Certified', value: '6' }, { label: 'Training', value: 'Current' }, { label: 'Next Training', value: 'Q3' }],
      details: ['6 active certified reviewers', 'All trained on v4 CrownDashboardTemplate standards', 'Last training: January 2026', 'Q3 refresher training planned'],
      primaryActionLabel: 'Reviewer Roster', backActionLabel: 'Training Materials',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: '8:20 AM' },
    { key: 'report', icon: 'RP', title: 'Certification Reports', status: 'Due', statusTone: 'warn',
      mainKpi: 'Q2 certification report due this week', summary: 'Quarterly summary for all stakeholders.',
      kpis: [{ label: 'Q2 Report', value: 'Due this week' }, { label: 'Certified', value: '41' }, { label: 'Rate', value: '91%' }, { label: 'YOY Change', value: '+29pts' }],
      details: ['Q2 certification summary due this week', '91% certification rate â€” up 29 points YOY', 'Report distribution: engineering, product, exec', 'Trend: consistent improvement each quarter'],
      primaryActionLabel: 'Publish Report', backActionLabel: 'Report History',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Certification growth', title: 'Dashboards Certified (Cumulative)', chip: '41 certified', trend: CERT_TREND },
    { kicker: 'Quality trend', title: 'First-Pass Certification Rate (%)', chip: '91% (March)', trend: RATE_TREND },
  ],

  activities: [
    '6 dashboards in review queue â€” assigned to reviewers.',
    '2 failed dashboards: correction feedback packages prepared.',
    'Q2 certification report drafted â€” publishing this week.',
    '41 dashboards certified at 91% first-pass rate.',
    'CrownDashboardTemplate v4 gold standard documentation current.',
  ],

  quickActions: [
    { label: 'Review Queue', href: '/dashboard-certification-center' },
    { label: 'Certified List', href: '/dashboard-certification-center' },
    { label: 'Failed Dashboards', href: '/dashboard-certification-center' },
    { label: 'Standards Docs', href: '/dashboard-certification-center' },
  ],

  statuses: [
    { label: 'Certified', state: '41 dashboards' },
    { label: 'In Review', state: '6 pending' },
    { label: 'Failed', state: '2 (corrections needed)' },
    { label: 'Cert Rate', state: '91% (target 90%)' },
  ],
};
