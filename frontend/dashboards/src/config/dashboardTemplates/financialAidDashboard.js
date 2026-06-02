const AID_TREND = [
  { month: 'Aug', value: 24 }, { month: 'Sep', value: 38 }, { month: 'Oct', value: 51 },
  { month: 'Nov', value: 63 }, { month: 'Dec', value: 70 }, { month: 'Jan', value: 74 },
  { month: 'Feb', value: 79 }, { month: 'Mar', value: 87 },
];
const DISB_TREND = [
  { month: 'Aug', value: 18 }, { month: 'Sep', value: 31 }, { month: 'Oct', value: 44 },
  { month: 'Nov', value: 55 }, { month: 'Dec', value: 60 }, { month: 'Jan', value: 66 },
  { month: 'Feb', value: 71 }, { month: 'Mar', value: 78 },
];

export default {
  key: 'financialAid',
  activePath: '/financial-aid-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'FA', name: 'Financial Aid Office', role: 'Finance â€” Financial Aid & Awards' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Financial Aid!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Financial aid widgets currently use template snapshots pending live aid service integration.',
  note: 'Certification remains in review until financial aid metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/financialAid/summary/',
  liveDataKey: 'financialAid',
  metrics: [
    { label: 'Aid Applications', value: '112', detail: '87 awarded â€” 25 in review or incomplete.', accent: 'blue' },
    { label: 'Awards Processed', value: '87', detail: '$210K disbursed YTD â€” on schedule.', accent: 'emerald' },
    { label: 'Disbursements Due', value: '$42K', detail: 'Next batch April 30 â€” 18 recipients.', accent: 'gold' },
    { label: 'Aid Utilization', value: '91%', detail: 'Budget: $230K â€” $210K disbursed to date.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Process 25 incomplete applications', detail: 'Families contacted â€” docs due by April 28.', state: 'This week', tone: 'warn' },
    { title: 'Prepare April 30 disbursement batch', detail: '18 recipients â€” final approval needed.', state: 'Today', tone: 'warn' },
    { title: 'Spring renewal letters', detail: '62 families up for renewal â€” letters ready to send.', state: 'Next week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Aid priorities',

  alerts: [
    { title: '3 applications flagged for income verification', detail: 'Supporting docs not received â€” families notified.', tone: 'warn' },
    { title: 'Disbursement batch requires admin approval', detail: '$42K batch pending signature before April 30.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'applications', icon: 'AP', title: 'Applications', status: 'In Review', statusTone: 'warn',
      mainKpi: '112 received â€” 87 awarded, 25 pending', summary: '25 incomplete apps in review â€” deadline April 28.',
      kpis: [{ label: 'Received', value: '112' }, { label: 'Awarded', value: '87' }, { label: 'In Review', value: '18' }, { label: 'Incomplete', value: '7' }],
      details: ['87 awards active this semester', '18 in committee review', '7 families missing documentation', '3 flagged for income verification'],
      primaryActionLabel: 'View Applications', backActionLabel: 'Open Finance',
      primaryActionHref: '/financial-aid-dashboard', backActionHref: '/finance', lastUpdated: '8:00 AM' },
    { key: 'awards', icon: 'AW', title: 'Award Management', status: 'On Track', statusTone: 'good',
      mainKpi: '$210K disbursed â€” 91% utilization', summary: 'Award disbursements on schedule for the semester.',
      kpis: [{ label: 'Awarded', value: '$210K' }, { label: 'Budget', value: '$230K' }, { label: 'Utilization', value: '91%' }, { label: 'Recipients', value: '87' }],
      details: ['87 active award recipients', 'Average award: $2,414', 'Largest award: $6,200', 'Minimum award: $500'],
      primaryActionLabel: 'Manage Awards', backActionLabel: 'View Reports',
      primaryActionHref: '/financial-aid-dashboard', backActionHref: '/finance', lastUpdated: '8:05 AM' },
    { key: 'disbursements', icon: 'DS', title: 'Disbursements', status: 'Pending Approval', statusTone: 'warn',
      mainKpi: '$42K batch due April 30', summary: 'April batch ready â€” admin signature required.',
      kpis: [{ label: 'Next Batch', value: '$42K' }, { label: 'Recipients', value: '18' }, { label: 'Avg Disbursement', value: '$2,333' }, { label: 'Status', value: 'Pending' }],
      details: ['18 recipients in April batch', '$42K total pending disbursal', 'Admin approval required before April 30', 'Payment method: direct deposit 14, check 4'],
      primaryActionLabel: 'Review Batch', backActionLabel: 'Open Finance',
      primaryActionHref: '/finance', backActionHref: '/finance', lastUpdated: '7:50 AM' },
    { key: 'renewals', icon: 'RN', title: 'Renewals', status: 'Upcoming', statusTone: 'good',
      mainKpi: '62 renewals due', summary: 'Spring renewal letters ready â€” send by May 1.',
      kpis: [{ label: 'Renewals Due', value: '62' }, { label: 'Auto-Renew', value: '31' }, { label: 'Review Required', value: '31' }, { label: 'Letters Ready', value: 'Yes' }],
      details: ['62 families up for annual renewal', '31 auto-renewing based on income stability', '31 require updated income verification', 'Renewal letters ready to send'],
      primaryActionLabel: 'Send Renewals', backActionLabel: 'View Reports',
      primaryActionHref: '/financial-aid-dashboard', backActionHref: '/finance', lastUpdated: '7:45 AM' },
    { key: 'compliance', icon: 'CL', title: 'Aid Compliance', status: 'Stable', statusTone: 'good',
      mainKpi: 'No compliance flags', summary: 'All aid records current â€” audit trail maintained.',
      kpis: [{ label: 'Audit Ready', value: 'Yes' }, { label: 'Flags', value: '0' }, { label: 'Records Complete', value: '87' }, { label: 'Last Audit', value: 'Feb 2026' }],
      details: ['All awarded families have complete files', 'Income verifications on file', 'IRS cross-check complete for top awards', 'Next audit scheduled Q4 2026'],
      primaryActionLabel: 'View Compliance', backActionLabel: 'Open Finance',
      primaryActionHref: '/financial-aid-dashboard', backActionHref: '/finance', lastUpdated: '8:10 AM' },
    { key: 'reporting', icon: 'RP', title: 'Aid Reports', status: 'Stable', statusTone: 'good',
      mainKpi: 'Q3 report ready', summary: 'Quarterly financial aid summary ready for board review.',
      kpis: [{ label: 'Reports Ready', value: '3' }, { label: 'YTD Awards', value: '$210K' }, { label: 'Utilization', value: '91%' }, { label: 'Families Served', value: '87' }],
      details: ['Q3 financial aid report generated', 'Board summary ready for May meeting', 'Impact report: 87 families supported', 'Budget variance: $20K remaining'],
      primaryActionLabel: 'View Reports', backActionLabel: 'Open Finance',
      primaryActionHref: '/finance', backActionHref: '/finance', lastUpdated: '8:15 AM' },
  ],

  trendPanels: [
    { kicker: 'Aid applications', title: 'Awards Processed YTD', chip: '87 awards active', trend: AID_TREND },
    { kicker: 'Aid disbursements', title: 'Funds Disbursed ($K)', chip: '$210K disbursed', trend: DISB_TREND },
  ],

  activities: [
    'April disbursement batch prepared â€” 18 recipients, $42K.',
    'Incomplete application follow-up sent to 7 families.',
    'Income verification flags raised for 3 applications.',
    'Spring renewal letters prepared for 62 families.',
    'Q3 financial aid report submitted for board review.',
  ],

  quickActions: [
    { label: 'View Applications', href: '/financial-aid-dashboard' },
    { label: 'Open Finance', href: '/finance' },
    { label: 'Process Disbursements', href: '/finance' },
    { label: 'Send Renewals', href: '/financial-aid-dashboard' },
  ],

  statuses: [
    { label: 'Aid System', state: 'Healthy' },
    { label: 'April Disbursement', state: 'Pending approval' },
    { label: 'Applications', state: '25 in review' },
    { label: 'Compliance', state: 'Clean' },
  ],
};

