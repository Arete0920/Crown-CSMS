import { LIVE_NOTE } from './_baseData.js';

const CERT_TREND = [
  { month: 'Aug', value: 0 }, { month: 'Sep', value: 0 }, { month: 'Oct', value: 0 },
  { month: 'Nov', value: 0 }, { month: 'Dec', value: 0 }, { month: 'Jan', value: 0 },
  { month: 'Feb', value: 0 }, { month: 'Mar', value: 0 },
];
const RATE_TREND = [
  { month: 'Aug', value: 0 }, { month: 'Sep', value: 0 }, { month: 'Oct', value: 0 },
  { month: 'Nov', value: 0 }, { month: 'Dec', value: 0 }, { month: 'Jan', value: 0 },
  { month: 'Feb', value: 0 }, { month: 'Mar', value: 0 },
];

export default {
  key: 'dashboardCertificationCenter',
  activePath: '/dashboard-certification-center',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'DC', name: 'Dashboard Certification Center', role: 'Platform — Dashboard Quality & Certification Authority' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Certification Center!',
  subtitle: 'Heritage Christian Academy',
  note: LIVE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/dashboard-certification-center/summary',
  liveDataKey: 'dashboardCertificationCenter',

  metrics: [
    { label: 'Dashboards Certified', value: '0', detail: '0 of 40 dashboards live-data certified.', accent: 'emerald' },
    { label: 'Mapped Only', value: '40', detail: '40 dashboard routes mapped; live-data certification still open.', accent: 'gold' },
    { label: 'Pending Review', value: '0', detail: 'No dashboards ready for independent certification review yet.', accent: 'navy' },
    { label: 'Cert Rate', value: '0%', detail: 'Certification rate remains 0% until evidence packets are approved.', accent: 'blue' },
  ],

  priorities: [
    { title: 'Assign Batch 0 dashboard owner', detail: 'Owner is still TBD for certification center governance.', state: 'Required', tone: 'warn' },
    { title: 'Assign independent reviewer', detail: 'TC cannot self-approve dashboard certification work.', state: 'Required', tone: 'warn' },
    { title: 'Wire proof state from the dashboard matrix', detail: 'Certification Center must report real matrix/evidence packet state before promotion.', state: 'Next', tone: 'nominal' },
  ],
  prioritiesTitle: 'Certification priorities',

  alerts: [
    { title: 'No dashboards are certified yet', detail: 'Current verified state remains 40 mapped dashboards and 0 live-data certified dashboards.', tone: 'warn' },
    { title: 'Owner and independent reviewer are still TBD', detail: 'Assign governance roles before certification promotion.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'certified', icon: 'CT', title: 'Certified Dashboards', status: 'Not Started', statusTone: 'warn',
      mainKpi: '0 certified — 0% certification rate', summary: 'Certification starts after summary APIs, tenant proof, permission proof, runtime proof, and independent review.',
      kpis: [{ label: 'Certified', value: '0' }, { label: 'Mapped', value: '40' }, { label: 'First-Pass Rate', value: '0%' }, { label: 'Target', value: '100%' }],
      details: ['0 dashboards live-data certified', '40 dashboards mapped only', 'No independent certification reviews complete', 'Certification Center must consume real proof state before promotion'],
      primaryActionLabel: 'Certification Matrix', backActionLabel: 'Evidence Packets',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: 'Pending live data' },
    { key: 'review', icon: 'RV', title: 'Review Queue', status: 'Not Ready', statusTone: 'warn',
      mainKpi: '0 dashboards in certification review', summary: 'Dashboards must reach runtime proof before independent review.',
      kpis: [{ label: 'In Queue', value: '0' }, { label: 'Assigned', value: 'TBD' }, { label: 'Avg Review Time', value: 'TBD' }, { label: 'SLA', value: 'TBD' }],
      details: ['Owner TBD', 'Reviewer TBD', 'Runtime proof pending', 'Evidence packets pending'],
      primaryActionLabel: 'Assign Reviewer', backActionLabel: 'Review Requirements',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: 'Pending governance assignment' },
    { key: 'failed', icon: 'FL', title: 'Failed Certification', status: 'None Submitted', statusTone: 'neutral',
      mainKpi: '0 failed — no dashboards submitted', summary: 'Failure reporting starts once dashboards enter independent review.',
      kpis: [{ label: 'Failed', value: '0' }, { label: 'Resubmit Deadline', value: 'TBD' }, { label: 'Issues', value: 'TBD' }, { label: 'Feedback', value: 'TBD' }],
      details: ['No dashboard has entered certification review', 'No failed certification packets exist', 'Correction workflow pending live proof state'],
      primaryActionLabel: 'Review Failures', backActionLabel: 'Correction Workflow',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: 'Not started' },
    { key: 'standards', icon: 'SD', title: 'Standards', status: 'Required', statusTone: 'warn',
      mainKpi: 'Required: summary API + evidence packet + independent review', summary: 'Certification must follow the dashboard completion project controls.',
      kpis: [{ label: 'Standard', value: 'Evidence-backed' }, { label: 'Version', value: 'Batch 0' }, { label: 'Required Proof', value: 'Tenant + Permission + Runtime' }, { label: 'Owner', value: 'TBD' }],
      details: ['Dashboard route/registry is not completion', 'Sample payload is not production proof', 'TC cannot self-approve certification', 'Evidence packet required before promotion'],
      primaryActionLabel: 'Standards Docs', backActionLabel: 'Template Guide',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: 'Batch 0 controls' },
    { key: 'training', icon: 'TR', title: 'Reviewer Training', status: 'TBD', statusTone: 'warn',
      mainKpi: 'Independent reviewer not assigned', summary: 'Reviewer identity and review procedure must be recorded before certification.',
      kpis: [{ label: 'Reviewers', value: 'TBD' }, { label: 'Certified', value: 'TBD' }, { label: 'Training', value: 'TBD' }, { label: 'Next Training', value: 'TBD' }],
      details: ['Reviewer assignment pending', 'Review criteria must include data, tenant, permission, runtime, and evidence proof', 'Governance review required before merge or promotion'],
      primaryActionLabel: 'Reviewer Roster', backActionLabel: 'Training Materials',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: 'Pending assignment' },
    { key: 'report', icon: 'RP', title: 'Certification Reports', status: 'Not Ready', statusTone: 'warn',
      mainKpi: 'No certification report until proof state is live', summary: 'Reports must be generated from the dashboard matrix and evidence packets.',
      kpis: [{ label: 'Report', value: 'Not ready' }, { label: 'Certified', value: '0' }, { label: 'Rate', value: '0%' }, { label: 'Evidence Packets', value: 'Pending' }],
      details: ['Dashboard matrix proof state not wired', 'Evidence packet status not wired', 'Independent review state not wired'],
      primaryActionLabel: 'Draft Report', backActionLabel: 'Report History',
      primaryActionHref: '/dashboard-certification-center', backActionHref: '/dashboard-certification-center', lastUpdated: 'Not ready' },
  ],

  trendPanels: [
    { kicker: 'Certification growth', title: 'Dashboards Certified (Cumulative)', chip: '0 certified', trend: CERT_TREND },
    { kicker: 'Quality trend', title: 'First-Pass Certification Rate (%)', chip: '0% until reviews begin', trend: RATE_TREND },
  ],

  activities: [
    '0 dashboards live-data certified.',
    '40 dashboards currently remain mapped-only.',
    'Batch 0 owners and independent reviewers are still TBD.',
    'Certification Center must be wired to real proof state before promotion.',
    'No dashboard certification claim may rely on sample or fallback data.',
  ],

  quickActions: [
    { label: 'Certification Matrix', href: '/dashboard-certification-center' },
    { label: 'Evidence Packets', href: '/dashboard-certification-center' },
    { label: 'Assign Reviewer', href: '/dashboard-certification-center' },
    { label: 'Standards Docs', href: '/dashboard-certification-center' },
  ],

  statuses: [
    { label: 'Certified', state: '0 dashboards' },
    { label: 'Mapped Only', state: '40 dashboards' },
    { label: 'In Review', state: '0 pending' },
    { label: 'Cert Rate', state: '0%' },
  ],
};