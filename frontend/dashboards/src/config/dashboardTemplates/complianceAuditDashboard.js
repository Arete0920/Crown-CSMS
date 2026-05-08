import { BASE_NOTE } from './_baseData.js';

const CONTROL_TREND = [
  { month: 'Aug', value: 68 }, { month: 'Sep', value: 72 }, { month: 'Oct', value: 76 },
  { month: 'Nov', value: 78 }, { month: 'Dec', value: 80 }, { month: 'Jan', value: 82 },
  { month: 'Feb', value: 84 }, { month: 'Mar', value: 86 },
];
const FINDING_TREND = [
  { month: 'Aug', value: 12 }, { month: 'Sep', value: 10 }, { month: 'Oct', value: 9 },
  { month: 'Nov', value: 8 }, { month: 'Dec', value: 7 }, { month: 'Jan', value: 6 },
  { month: 'Feb', value: 5 }, { month: 'Mar', value: 4 },
];

export default {
  key: 'complianceAudit',
  activePath: '/compliance-audit-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'CA', name: 'Compliance & Audit', role: 'Platform — Compliance Monitoring & Internal Audit' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Compliance Team!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  metrics: [
    { label: 'Active Audits', value: '3', detail: 'Diocese, State Accreditation, and SOC2 Type II in progress.', accent: 'navy' },
    { label: 'Controls Passing', value: '86%', detail: '86 of 100 active controls passing.', accent: 'emerald' },
    { label: 'Open Findings', value: '4', detail: '4 findings requiring remediation plans.', accent: 'gold' },
    { label: 'Reviews Due (30d)', value: '6', detail: '6 compliance reviews due in next 30 days.', accent: 'blue' },
  ],

  priorities: [
    { title: 'Submit Diocese audit evidence package', detail: 'Diocese audit window April 14–18 — evidence due April 13.', state: 'This week', tone: 'warn' },
    { title: 'Remediate 4 open findings', detail: 'All 4 findings need documented remediation plans by April 20.', state: 'This week', tone: 'warn' },
    { title: 'Schedule 6 upcoming compliance reviews', detail: 'State, diocese, and internal — all due in 30 days.', state: 'This week', tone: 'nominal' },
  ],
  prioritiesTitle: 'Compliance priorities',

  alerts: [
    { title: 'Diocese evidence package due April 13', detail: 'Audit window April 14–18 — final evidence submission deadline.', tone: 'warn' },
    { title: '4 open findings need remediation plans', detail: 'Plans due April 20 — assign owners today.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'audits', icon: 'AU', title: 'Active Audits', status: 'In Progress', statusTone: 'warn',
      mainKpi: '3 active audits — Diocese, State, SOC2', summary: 'Diocese most urgent — evidence due April 13.',
      kpis: [{ label: 'Active', value: '3' }, { label: 'Diocese', value: 'Due Apr 13' }, { label: 'State Accred.', value: 'May 1' }, { label: 'SOC2 Type II', value: 'June 15' }],
      details: ['Diocese audit: evidence package due April 13', 'State accreditation: evidence due May 1', 'SOC2 Type II: fieldwork June 15–30', 'All three auditors confirmed'],
      primaryActionLabel: 'Audit Tracker', backActionLabel: 'Evidence',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: '8:00 AM' },
    { key: 'controls', icon: 'CT', title: 'Controls', status: 'Good', statusTone: 'good',
      mainKpi: '86/100 controls passing', summary: 'Control framework trending upward — 14 needing attention.',
      kpis: [{ label: 'Passing', value: '86' }, { label: 'Total', value: '100' }, { label: 'Failing', value: '4' }, { label: 'Testing', value: '10' }],
      details: ['86 controls passing', '4 controls with open findings', '10 controls in active testing cycle', 'Control score: 86 — up 18 points YOY'],
      primaryActionLabel: 'Control Matrix', backActionLabel: 'Test Results',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: '8:05 AM' },
    { key: 'findings', icon: 'FN', title: 'Findings', status: 'Action Required', statusTone: 'warn',
      mainKpi: '4 open findings — plans due April 20', summary: 'Assign owners and document remediation plans.',
      kpis: [{ label: 'Open', value: '4' }, { label: 'Critical', value: '1' }, { label: 'Moderate', value: '3' }, { label: 'Plans Due', value: 'Apr 20' }],
      details: ['Finding F-01 (Critical): Access control exception — assign April 15', 'Finding F-02: Training record gaps — moderate', 'Finding F-03: Data retention policy — moderate', 'Finding F-04: Vendor assessment — moderate'],
      primaryActionLabel: 'Finding Register', backActionLabel: 'Assign Owners',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: '8:10 AM' },
    { key: 'reviews', icon: 'RV', title: 'Compliance Reviews', status: 'Due Soon', statusTone: 'warn',
      mainKpi: '6 reviews due in 30 days', summary: 'Schedule all 6 — diocese, state, and internal cycles.',
      kpis: [{ label: 'Due (30d)', value: '6' }, { label: 'Diocese', value: '2' }, { label: 'State', value: '2' }, { label: 'Internal', value: '2' }],
      details: ['2 diocese compliance reviews due', '2 state regulatory reviews due', '2 internal control reviews scheduled', 'Review calendar updated and assigned'],
      primaryActionLabel: 'Review Schedule', backActionLabel: 'Compliance Calendar',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: '8:15 AM' },
    { key: 'evidence', icon: 'EV', title: 'Evidence Management', status: 'Active', statusTone: 'good',
      mainKpi: 'Evidence collection active for all 3 audits', summary: 'Diocese package 80% complete — due April 13.',
      kpis: [{ label: 'Diocese Package', value: '80%' }, { label: 'State Package', value: '40%' }, { label: 'SOC2 Package', value: '20%' }, { label: 'Docs Collected', value: '184' }],
      details: ['184 evidence documents collected YTD', 'Diocese: 80% — final 5 docs due tomorrow', 'State accreditation: 40% — on track for May 1', 'SOC2: 20% — fieldwork begins June 15'],
      primaryActionLabel: 'Evidence Vault', backActionLabel: 'Upload',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: '8:20 AM' },
    { key: 'policies', icon: 'PL', title: 'Policy Management', status: 'Current', statusTone: 'good',
      mainKpi: 'All policies reviewed and current', summary: 'Annual policy review complete — next cycle August.',
      kpis: [{ label: 'Policies Active', value: '42' }, { label: 'Reviewed', value: '42' }, { label: 'Updates', value: '6' }, { label: 'Next Review', value: 'Aug 2026' }],
      details: ['42 active organizational policies', '6 policies updated in annual review', 'Data retention policy: minor update pending', 'All policies posted to staff portal'],
      primaryActionLabel: 'Policy Library', backActionLabel: 'Review History',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Control framework', title: 'Controls Passing (%)', chip: '86% (up 18 YOY)', trend: CONTROL_TREND },
    { kicker: 'Finding reduction', title: 'Open Findings Per Month', chip: '4 open', trend: FINDING_TREND },
  ],

  activities: [
    'Diocese audit evidence package at 80% — due April 13.',
    '4 open findings assigned owners — remediation plans due April 20.',
    '6 compliance reviews scheduled for next 30 days.',
    'SOC2 Type II fieldwork confirmed for June 15.',
    'Annual policy review complete — 6 policies updated.',
  ],

  quickActions: [
    { label: 'Audit Tracker', href: '/compliance-audit-dashboard' },
    { label: 'Finding Register', href: '/compliance-audit-dashboard' },
    { label: 'Evidence Vault', href: '/compliance-audit-dashboard' },
    { label: 'Control Matrix', href: '/compliance-audit-dashboard' },
  ],

  statuses: [
    { label: 'Active Audits', state: '3 in progress' },
    { label: 'Controls', state: '86/100 passing' },
    { label: 'Open Findings', state: '4 (1 critical)' },
    { label: 'Diocese Package', state: '80% (due Apr 13)' },
  ],
};
