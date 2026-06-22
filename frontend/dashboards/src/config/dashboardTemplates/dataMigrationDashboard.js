import { LIVE_NOTE } from './_baseData.js';

const RECORDS_TREND = [
  { month: 'Aug', value: 0 }, { month: 'Sep', value: 8400 }, { month: 'Oct', value: 16800 },
  { month: 'Nov', value: 24200 }, { month: 'Dec', value: 28600 }, { month: 'Jan', value: 34400 },
  { month: 'Feb', value: 41800 }, { month: 'Mar', value: 48200 },
];
const ERR_TREND = [
  { month: 'Aug', value: 0 }, { month: 'Sep', value: 84 }, { month: 'Oct', value: 72 },
  { month: 'Nov', value: 58 }, { month: 'Dec', value: 44 }, { month: 'Jan', value: 36 },
  { month: 'Feb', value: 28 }, { month: 'Mar', value: 14 },
];

export default {
  key: 'dataMigration',
  activePath: '/data-migration-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'DM', name: 'Data Migration', role: 'Platform â€” School Data Migration & Legacy System Conversion' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Data Migration Team!',
  subtitle: 'Heritage Christian Academy',
  note: LIVE_NOTE,
  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/data-migration/summary',
  liveDataKey: 'dataMigration',

  metrics: [
    { label: 'Records Migrated', value: '48,200', detail: 'YTD â€” across 9 completed school migrations.', accent: 'emerald' },
    { label: 'Validation Rate', value: '99.97%', detail: '48,186 of 48,200 records validated clean.', accent: 'blue' },
    { label: 'Errors Remaining', value: '14', detail: '14 records with unresolved validation issues.', accent: 'gold' },
    { label: 'Pending Migrations', value: '3', detail: 'Jefferson, Covenant, Grace â€” in pipeline.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Resolve 14 validation errors', detail: 'All 14 are blocking Jefferson go-live â€” clear today.', state: 'Today', tone: 'warn' },
    { title: 'Start Covenant school migration batch', detail: 'Data received and mapped â€” begin import pipeline.', state: 'This week', tone: 'nominal' },
    { title: 'Grace data format mapping', detail: 'File format mismatch â€” work with Grace IT to convert.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Data migration priorities',

  alerts: [
    { title: '14 Jefferson validation errors blocking go-live', detail: 'All 14 must clear before go-live â€” resolve today.', tone: 'warn' },
    { title: 'Grace data format incompatible â€” conversion needed', detail: 'Grace submitted CSV in old format â€” transform script needed.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'progress', icon: 'PG', title: 'Migration Progress', status: 'On Track', statusTone: 'good',
      mainKpi: '48,200 records migrated YTD', summary: 'Steady progress â€” error rate declining each month.',
      kpis: [{ label: 'Migrated', value: '48,200' }, { label: 'Validated', value: '48,186' }, { label: 'Error Rate', value: '0.03%' }, { label: 'Schools Done', value: '9' }],
      details: ['48,200 total records migrated YTD', '9 schools fully migrated and live', '14 validation errors remaining', 'Error rate trending down to 0.03%'],
      primaryActionLabel: 'Migration Log', backActionLabel: 'School Status',
      primaryActionHref: '/data-migration-dashboard', backActionHref: '/implementation-success-dashboard', lastUpdated: '8:00 AM' },
    { key: 'errors', icon: 'ER', title: 'Validation Errors', status: 'Action Required', statusTone: 'warn',
      mainKpi: '14 errors â€” all Jefferson, blocking go-live', summary: 'Must resolve today â€” May 1 deadline.',
      kpis: [{ label: 'Open Errors', value: '14' }, { label: 'School', value: 'Jefferson' }, { label: 'Type', value: 'Address + DOB' }, { label: 'Priority', value: 'Critical' }],
      details: ['14 Jefferson records with validation issues', '11 address format errors â€” reformatting in progress', '3 date-of-birth format mismatches', 'All 14 must clear before go-live'],
      primaryActionLabel: 'Error Queue', backActionLabel: 'Resolve',
      primaryActionHref: '/data-migration-dashboard', backActionHref: '/data-migration-dashboard', lastUpdated: '8:05 AM' },
    { key: 'pipeline', icon: 'PP', title: 'Pipeline', status: 'Active', statusTone: 'good',
      mainKpi: '3 migrations pending â€” Jefferson, Covenant, Grace', summary: 'All three targeting May 1 go-live.',
      kpis: [{ label: 'In Pipeline', value: '3' }, { label: 'Jefferson', value: 'Final review' }, { label: 'Covenant', value: 'Import ready' }, { label: 'Grace', value: 'Format fix' }],
      details: ['Jefferson: 14 errors remaining â€” final review', 'Covenant: data mapped â€” ready for import pipeline', 'Grace: file format incompatible â€” conversion needed', 'All targeting May 1 go-live'],
      primaryActionLabel: 'Pipeline Status', backActionLabel: 'School Detail',
      primaryActionHref: '/data-migration-dashboard', backActionHref: '/data-migration-dashboard', lastUpdated: '8:10 AM' },
    { key: 'validation', icon: 'VL', title: 'Validation Engine', status: 'Running', statusTone: 'good',
      mainKpi: '99.97% clean rate', summary: 'Validation engine running â€” error detection improving.',
      kpis: [{ label: 'Clean Rate', value: '99.97%' }, { label: 'Rules Active', value: '84' }, { label: 'Checks/Hour', value: '1,200' }, { label: 'Uptime', value: '100%' }],
      details: ['84 validation rules active', 'Validation engine 100% uptime this month', '1,200 records processed per hour', 'New rule added: duplicate student ID detection'],
      primaryActionLabel: 'Validation Config', backActionLabel: 'Error Rules',
      primaryActionHref: '/data-migration-dashboard', backActionHref: '/data-migration-dashboard', lastUpdated: '8:15 AM' },
    { key: 'legacy', icon: 'LG', title: 'Legacy Systems', status: 'Decommissioning', statusTone: 'good',
      mainKpi: '6 of 9 legacy systems decommissioned', summary: 'Steady decommission progress â€” 3 remaining.',
      kpis: [{ label: 'Decommissioned', value: '6' }, { label: 'Remaining', value: '3' }, { label: 'Active', value: 'Read-only' }, { label: 'Target', value: 'June 30' }],
      details: ['6 legacy systems decommissioned', '3 remaining in read-only state', 'Target full decommission: June 30', 'Data archive completed for all decommissioned systems'],
      primaryActionLabel: 'Legacy Status', backActionLabel: 'Archive Log',
      primaryActionHref: '/data-migration-dashboard', backActionHref: '/data-migration-dashboard', lastUpdated: '8:20 AM' },
    { key: 'quality', icon: 'QA', title: 'Data Quality', status: 'Strong', statusTone: 'good',
      mainKpi: 'Highest data quality score in program history', summary: '99.97% clean â€” error rate down 83% YOY.',
      kpis: [{ label: 'Clean Rate', value: '99.97%' }, { label: 'YOY Improvement', value: '+83%' }, { label: 'Completeness', value: '99.8%' }, { label: 'Accuracy', value: '99.9%' }],
      details: ['Data quality at program-best levels', 'Error rate down 83% year-over-year', '99.8% field completeness', '99.9% cross-reference accuracy'],
      primaryActionLabel: 'Quality Report', backActionLabel: 'Historical',
      primaryActionHref: '/data-migration-dashboard', backActionHref: '/data-migration-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Migration volume', title: 'Cumulative Records Migrated', chip: '48,200 YTD', trend: RECORDS_TREND },
    { kicker: 'Error reduction', title: 'Monthly Validation Errors', chip: '14 remaining', trend: ERR_TREND },
  ],

  activities: [
    '14 Jefferson validation errors queued for resolution â€” go-live at risk.',
    'Covenant migration pipeline staged â€” ready for import batch run.',
    'Grace data format incompatibility identified â€” conversion script in progress.',
    '99.97% validation clean rate â€” program-best quality.',
    '6 legacy systems decommissioned â€” 3 remaining in read-only.',
  ],

  quickActions: [
    { label: 'Error Queue', href: '/data-migration-dashboard' },
    { label: 'Pipeline Status', href: '/data-migration-dashboard' },
    { label: 'Validation Config', href: '/data-migration-dashboard' },
    { label: 'Implementation', href: '/implementation-success-dashboard' },
  ],

  statuses: [
    { label: 'Records Migrated', state: '48,200 YTD' },
    { label: 'Validation Errors', state: '14 (critical)' },
    { label: 'Pending Schools', state: '3 in pipeline' },
    { label: 'Legacy Systems', state: '6/9 decommissioned' },
  ],
};
