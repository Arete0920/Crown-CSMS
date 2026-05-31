import { BASE_NOTE } from './_baseData.js';

const VISIT_TREND = [
  { month: 'Sep', value: 11 }, { month: 'Oct', value: 13 }, { month: 'Nov', value: 12 },
  { month: 'Dec', value: 14 }, { month: 'Jan', value: 13 }, { month: 'Feb', value: 14 }, { month: 'Mar', value: 14 },
];
const COMPLIANCE_TREND = [
  { month: 'Sep', value: 92 }, { month: 'Oct', value: 93 }, { month: 'Nov', value: 94 },
  { month: 'Dec', value: 95 }, { month: 'Jan', value: 95 }, { month: 'Feb', value: 96 }, { month: 'Mar', value: 96 },
];

export default {
  key: 'health',
  activePath: '/health',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'NU', name: 'School Nurse', role: 'Health â€” Care & Compliance' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Nurse!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/health/summary/',
  liveDataKey: 'health',
  metrics: [
    { label: 'Visits Today', value: '14', detail: 'Above 4-week average â€” monitor through afternoon.', accent: 'gold' },
    { label: 'Medications Administered', value: '9', detail: 'All scheduled doses delivered on time.', accent: 'emerald' },
    { label: 'Immunizations Missing', value: '6', detail: 'Parent follow-up needed before Friday.', accent: 'gold' },
    { label: 'Incident Reports This Week', value: '2', detail: 'Both reviewed â€” administrator notified.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Follow up on 6 missing immunization records', detail: 'Send parent letters today â€” compliance check Friday.', state: 'Today', tone: 'warn' },
    { title: 'Refill inhaler stock', detail: 'Stock low â€” order before Friday.', state: 'This week', tone: 'warn' },
    { title: 'Confirm parent callback for Sofia Medina', detail: 'Sent home this morning â€” log outcome.', state: 'Today', tone: 'warn' },
  ],
  prioritiesTitle: 'Health office priorities',

  alerts: [
    { title: '6 immunization records incomplete', detail: 'Parent follow-up needed before compliance audit.', tone: 'warn' },
    { title: '2 student physicals expire this month', detail: 'Coordinate parent reminders this week.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'visits', icon: 'VS', title: "Today's Visits", status: 'Watch', statusTone: 'warn',
      mainKpi: '14 visits today', summary: 'Visit volume above average â€” afternoon staffing confirmed.',
      kpis: [{ label: 'Total visits', value: '14' }, { label: 'Sent home', value: '1' }, { label: 'Returned to class', value: '12' }, { label: 'Follow-up', value: '1' }],
      details: ['Elijah Turner (G9) â€” headache â€” sent home', 'Sofia Medina (G11) â€” stomach â€” returned', 'Marcus Brown (G7) â€” asthma inhaler â€” returned', 'Ava Chen (G10) â€” ankle twist â€” ice + rest'],
      primaryActionLabel: 'Open Visit Log', backActionLabel: 'Visit Reports',
      primaryActionHref: '/health', backActionHref: '/reports', lastUpdated: '8:30 AM' },
    { key: 'medications', icon: 'MD', title: 'Medication Log', status: 'Stable', statusTone: 'good',
      mainKpi: '9 doses administered', summary: 'All scheduled doses delivered. Inhaler stock running low.',
      kpis: [{ label: 'Doses today', value: '9' }, { label: 'Students on med', value: '9' }, { label: 'Standing orders', value: '4' }, { label: 'Stock alerts', value: '1' }],
      details: ['Albuterol inhaler â€” 3 students / 3 doses', 'EpiPen on file â€” 1 student / 0 doses', 'ADHD daily med â€” 4 students / 4 doses', 'Insulin injection â€” 1 student / 1 dose'],
      primaryActionLabel: 'Open Medication Log', backActionLabel: 'Stock Alerts',
      primaryActionHref: '/health', backActionHref: '/health', lastUpdated: '8:15 AM' },
    { key: 'immunizations', icon: 'IM', title: 'Immunization Compliance', status: 'Watch', statusTone: 'warn',
      mainKpi: '6 records missing', summary: 'Compliance trending up; 6 students still incomplete.',
      kpis: [{ label: 'Compliant', value: '153' }, { label: 'Missing', value: '6' }, { label: 'Compliance %', value: '96%' }, { label: 'Audit due', value: 'Apr 1' }],
      details: ['Grade 7 â€” 2 records missing', 'Grade 8 â€” 1 record missing', 'Grade 9 â€” 1 record missing', 'Grade 10 â€” 2 records missing'],
      primaryActionLabel: 'Open Immunization Log', backActionLabel: 'Parent Outreach',
      primaryActionHref: '/health', backActionHref: '/communications', lastUpdated: '8:00 AM' },
    { key: 'incidents', icon: 'IC', title: 'Incident Reports', status: 'Stable', statusTone: 'good',
      mainKpi: '2 reports this week', summary: 'Both reports filed and acknowledged by administration.',
      kpis: [{ label: 'This week', value: '2' }, { label: 'MTD', value: '5' }, { label: 'Open follow-ups', value: '0' }, { label: 'Reported to admin', value: '2' }],
      details: ['Both this week filed and acknowledged', 'No open incident follow-ups outstanding', '5 incident reports filed month to date', 'Quarterly incident review scheduled Apr 8'],
      primaryActionLabel: 'Open Incident Log', backActionLabel: 'Reports',
      primaryActionHref: '/health', backActionHref: '/reports', lastUpdated: '7:50 AM' },
    { key: 'parent-comms', icon: 'PC', title: 'Parent Communications', status: 'Watch', statusTone: 'warn',
      mainKpi: '1 callback pending', summary: 'Sofia Medina sent home â€” parent callback expected.',
      kpis: [{ label: 'Callbacks pending', value: '1' }, { label: 'Letters today', value: '6' }, { label: 'Forms received', value: '3' }, { label: 'Forms outstanding', value: '6' }],
      details: ['Pending callback â€” Sofia Medina (sent home)', '6 immunization parent letters going out today', '3 health forms received this week', '6 forms still outstanding'],
      primaryActionLabel: 'Open Communications', backActionLabel: 'Form Library',
      primaryActionHref: '/communications', backActionHref: '/health', lastUpdated: '7:35 AM' },
    { key: 'inventory', icon: 'IN', title: 'Inventory & Supplies', status: 'Watch', statusTone: 'warn',
      mainKpi: 'Inhaler refill needed', summary: 'Refill order for inhaler stock recommended this week.',
      kpis: [{ label: 'Low items', value: '1' }, { label: 'Out of stock', value: '0' }, { label: 'Order pending', value: '1' }, { label: 'Vendors', value: '2' }],
      details: ['Inhaler stock â€” refill needed this week', 'Other supplies stocked above safety floor', 'Order draft prepared for office approval', 'Standing supply order ships monthly'],
      primaryActionLabel: 'Open Inventory', backActionLabel: 'Vendor List',
      primaryActionHref: '/health', backActionHref: '/finance', lastUpdated: '7:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Visit trend', title: 'Average daily visits by month', chip: 'Steady', trend: VISIT_TREND },
    { kicker: 'Compliance trend', title: 'Immunization compliance % by month', chip: 'Climbing', trend: COMPLIANCE_TREND },
  ],

  activityKicker: 'Health office activity',
  activityTitle: 'Recent health events',
  activities: [
    'Elijah Turner sent home with headache.',
    '9 medications administered on schedule.',
    'Ankle injury report filed for Ava Chen.',
    'Inhaler stock flagged for refill.',
    'Quarterly incident review scheduled for April.',
  ],

  quickActions: [
    { title: 'Open Communications', eyebrow: 'Quick action', description: 'Send parent letters and follow-ups.', actionLabel: 'Open Communications', href: '/communications', allowedRoles: ['health'] },
    { title: 'Open Counseling', eyebrow: 'Quick action', description: 'Coordinate care handoffs with counseling team.', actionLabel: 'Open Counseling', href: '/counseling', allowedRoles: ['health'] },
    { title: 'Reports', eyebrow: 'Quick action', description: 'Review incident, visit, and compliance reports.', actionLabel: 'Open Reports', href: '/reports', allowedRoles: ['health'] },
    { title: 'Open Health', eyebrow: 'Quick action', description: 'Return to the Health Office command center.', actionLabel: 'Open Health', href: '/health', allowedRoles: ['health'] },
  ],

  statusTitle: 'Health workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'Visit Log', state: 'Current' },
    { label: 'Medication Log', state: 'Synced' },
    { label: 'Immunization Records', state: '96%' },
    { label: 'Inventory', state: 'Watch' },
  ],
};

