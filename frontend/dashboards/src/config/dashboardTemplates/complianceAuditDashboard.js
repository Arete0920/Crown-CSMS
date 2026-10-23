// Fictional Heritage school training data. Never present this fixture as an
// Arete/CROWN audit result, a scheduled examination, or a CPA SOC 2 report.
const SAMPLE_CONTROL_TREND = [
  { month: 'Aug', value: 4 },
  { month: 'Sep', value: 6 },
  { month: 'Oct', value: 8 },
];
const SAMPLE_FINDING_TREND = [
  { month: 'Aug', value: 6 },
  { month: 'Sep', value: 5 },
  { month: 'Oct', value: 4 },
];

export default {
  key: 'complianceAudit',
  activePath: '/compliance-audit-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 0,
  user: { initials: 'CA', name: 'Compliance & Audit', role: 'School Compliance — Training View' },
  eyebrow: 'Fictional Heritage School — Demonstration Only',
  title: 'Good morning, Compliance Team!',
  subtitle: 'Illustrative school review workflow; no live audit evidence asserted',
  dataState: 'fallback',
  sourceLabel: 'Fictional school demonstration data; not verified audit or compliance evidence.',
  note: 'Fictional school preview. No SOC 2 Type I or Type II report, CPA engagement, or audit completion is asserted for CROWN.',
  // The summary service can provide real school data, but may also identify
  // backend sample payloads. Template cards remain sample-only in either case.
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/complianceAudit/summary/',
  liveDataKey: 'complianceAudit',

  metrics: [
    { label: 'Example Review Items', value: '12', detail: 'Fictional school planning queue; not a count of audited controls.', accent: 'navy' },
    { label: 'Example Policies Due', value: '6', detail: 'Illustrative school policy tasks; not adopted Arete policies.', accent: 'blue' },
    { label: 'Example Findings', value: '4', detail: 'Synthetic demonstration findings; no independent auditor findings represented.', accent: 'gold' },
    { label: 'CROWN SOC 2 Assurance', value: 'Not attested', detail: 'No independent SOC 2 Type I or Type II report established.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Review sample policy acknowledgments', detail: 'Training scenario only; no real deadline or review assigned.', state: 'Sample', tone: 'warn' },
    { title: 'Practice evidence-request intake', detail: 'Demonstration exercise without customer records.', state: 'Sample', tone: 'warn' },
  ],
  prioritiesTitle: 'Illustrative school compliance tasks',

  alerts: [
    { title: 'Example finding requires review', detail: 'Synthetic school scenario; no real security finding implied.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'audits', icon: 'AU', title: 'School Review Planner', status: 'Sample', statusTone: 'warn',
      mainKpi: 'Example audit-planning queue', summary: 'Fictional school-only work; no external auditor or fieldwork confirmed.',
      kpis: [{ label: 'Example Reviews', value: '3' }, { label: 'External SOC 2', value: 'Not scheduled' }],
      details: ['Example internal school review', 'No CPA fieldwork is represented', 'No issued SOC 2 report is implied'],
      primaryActionLabel: 'Review Planner', backActionLabel: 'Example Evidence',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: 'Demo data' },
    { key: 'controls', icon: 'CT', title: 'Sample Control Checklist', status: 'Sample', statusTone: 'warn',
      mainKpi: 'Example checklists, not tested CROWN controls', summary: 'Illustrative exercise; no assurance scoring.',
      kpis: [{ label: 'Example Checks', value: '12' }, { label: 'Example Reviews Due', value: '6' }],
      details: ['Control checklist exercise', 'Operational results require a dated evidence record'],
      primaryActionLabel: 'Example Matrix', backActionLabel: 'Example Results',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: 'Demo data' },
    { key: 'findings', icon: 'FN', title: 'Example Findings', status: 'Sample', statusTone: 'warn',
      mainKpi: '4 fictional follow-up items', summary: 'Sample school review workflow only.',
      kpis: [{ label: 'Example Open', value: '4' }, { label: 'Actual Findings', value: 'Not supplied' }],
      details: ['Track a sample corrective action', 'Reassess once real findings and evidence are available'],
      primaryActionLabel: 'Example Register', backActionLabel: 'Example Actions',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: 'Demo data' },
    { key: 'reviews', icon: 'RV', title: 'Sample Review Calendar', status: 'Sample', statusTone: 'warn',
      mainKpi: 'Illustrative review schedule', summary: 'No actual external deadlines are represented.',
      kpis: [{ label: 'Example Reviews', value: '3' }, { label: 'Confirmed Auditors', value: 'None' }],
      details: ['Illustrative internal meeting', 'Dates must be verified before real scheduling'],
      primaryActionLabel: 'Example Calendar', backActionLabel: 'Review Examples',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: 'Demo data' },
    { key: 'evidence', icon: 'EV', title: 'Example Evidence Intake', status: 'Sample', statusTone: 'warn',
      mainKpi: 'Training evidence workflow', summary: 'No live SOC 2 evidence completeness percentage is claimed.',
      kpis: [{ label: 'Practice Items', value: '8' }, { label: 'SOC 2 Report', value: 'Not issued' }],
      details: ['Practice upload and review steps with synthetic examples', 'Private evidence requires controlled storage and reviewer sign-off'],
      primaryActionLabel: 'Example Evidence', backActionLabel: 'Example Intake',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: 'Demo data' },
    { key: 'policies', icon: 'PL', title: 'School Policy Examples', status: 'Sample', statusTone: 'warn',
      mainKpi: 'Illustrative policy library', summary: 'No management approval or completed review asserted.',
      kpis: [{ label: 'Example Policies', value: '6' }, { label: 'Actual Approved', value: 'Not supplied' }],
      details: ['Practice policy versioning and acknowledgment', 'Real approvals require names, versions and effective dates'],
      primaryActionLabel: 'Example Policies', backActionLabel: 'Example History',
      primaryActionHref: '/compliance-audit-dashboard', backActionHref: '/compliance-audit-dashboard', lastUpdated: 'Demo data' },
  ],

  trendPanels: [
    { kicker: 'Fictional training series', title: 'Example Checklist Activity', chip: 'Sample values only', trend: SAMPLE_CONTROL_TREND },
    { kicker: 'Fictional training series', title: 'Example Follow-up Items', chip: 'Sample values only', trend: SAMPLE_FINDING_TREND },
  ],

  activities: [
    'Illustrative school-only policy review exercise.',
    'Sample evidence intake; no real attestations or audit fieldwork.',
    'No independent SOC 2 examination is represented by this dashboard.',
  ],
  quickActions: [
    { label: 'Sample Review Planner', href: '/compliance-audit-dashboard' },
    { label: 'Sample Evidence Intake', href: '/compliance-audit-dashboard' },
  ],
  statuses: [
    { label: 'Record Type', state: 'Fictional school example' },
    { label: 'CROWN SOC 2 Report', state: 'Not issued or verified' },
    { label: 'External Auditor', state: 'Not established' },
  ],
};
