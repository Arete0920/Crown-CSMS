const PD_TREND = [
  { month: 'Aug', value: 12 }, { month: 'Sep', value: 18 }, { month: 'Oct', value: 22 },
  { month: 'Nov', value: 21 }, { month: 'Dec', value: 19 }, { month: 'Jan', value: 24 },
  { month: 'Feb', value: 26 }, { month: 'Mar', value: 28 },
];
const OBS_TREND = [
  { month: 'Aug', value: 2 }, { month: 'Sep', value: 4 }, { month: 'Oct', value: 6 },
  { month: 'Nov', value: 5 }, { month: 'Dec', value: 3 }, { month: 'Jan', value: 6 },
  { month: 'Feb', value: 8 }, { month: 'Mar', value: 8 },
];

export default {
  key: 'curriculumPD',
  activePath: '/curriculum-pd-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 3,
  user: { initials: 'CP', name: 'Curriculum & PD', role: 'Academics â€” Curriculum Development & Professional Development' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Curriculum Team!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Curriculum and professional development widgets currently use template snapshots pending live service integration.',
  note: 'Certification remains in review until curriculum and professional development metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/curriculumPD/summary/',
  liveDataKey: 'curriculumPD',
  metrics: [
    { label: 'Active PD Tracks', value: '6', detail: 'Differentiation, Literacy, STEM, Faith Integration, Tech, Leadership.', accent: 'blue' },
    { label: 'Teachers Enrolled', value: '42', detail: '100% of full-time faculty â€” all tracks active.', accent: 'emerald' },
    { label: 'Observations Due', value: '8', detail: '8 formal classroom observations remaining this semester.', accent: 'gold' },
    { label: 'Resources Published', value: '124', detail: 'Curriculum materials published to shared resource hub.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Complete 8 remaining classroom observations', detail: 'Semester deadline May 30 â€” schedule with teachers now.', state: 'This week', tone: 'warn' },
    { title: 'Finalize Q4 curriculum map updates', detail: '3 subject areas need updated unit maps before May 1.', state: 'This week', tone: 'warn' },
    { title: 'Plan summer PD retreat agenda', detail: '2-day retreat July 10â€“11 â€” initial agenda due June 1.', state: 'Next month', tone: 'nominal' },
  ],
  prioritiesTitle: 'Curriculum priorities',

  alerts: [
    { title: '8 classroom observations not yet scheduled', detail: 'Semester observation cycle closes May 30 â€” schedule now.', tone: 'warn' },
    { title: 'Q4 curriculum maps incomplete in 3 areas', detail: 'Math, Science, Language Arts updates needed by May 1.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'pdTracks', icon: 'PD', title: 'PD Tracks', status: 'Active', statusTone: 'good',
      mainKpi: '6 tracks â€” 42 teachers enrolled', summary: 'All faculty enrolled â€” 100% PD participation.',
      kpis: [{ label: 'Tracks', value: '6' }, { label: 'Teachers', value: '42' }, { label: 'Completion', value: '68%' }, { label: 'Hours Logged', value: '312' }],
      details: ['6 PD tracks across school-wide focus areas', '42 full-time teachers enrolled', '68% of required hours logged YTD', '312 total PD hours logged this year'],
      primaryActionLabel: 'PD Dashboard', backActionLabel: 'Track Details',
      primaryActionHref: '/curriculum-pd-dashboard', backActionHref: '/curriculum-pd-dashboard', lastUpdated: '8:00 AM' },
    { key: 'observations', icon: 'OB', title: 'Observations', status: 'Behind', statusTone: 'warn',
      mainKpi: '8 formal observations remaining', summary: 'Semester deadline May 30 â€” schedule this week.',
      kpis: [{ label: 'Remaining', value: '8' }, { label: 'Completed', value: '34' }, { label: 'Target', value: '42' }, { label: 'Deadline', value: 'May 30' }],
      details: ['34 of 42 required observations complete', '8 remaining â€” all need scheduling', 'Semester observation cycle closes May 30', 'Post-observation conferences required within 5 days'],
      primaryActionLabel: 'Schedule Observations', backActionLabel: 'View Log',
      primaryActionHref: '/curriculum-pd-dashboard', backActionHref: '/curriculum-pd-dashboard', lastUpdated: '8:05 AM' },
    { key: 'curriculum', icon: 'CM', title: 'Curriculum Maps', status: 'Watch', statusTone: 'warn',
      mainKpi: '3 subject maps need Q4 update', summary: 'Math, Science, Language Arts maps need updates by May 1.',
      kpis: [{ label: 'Maps Published', value: '24' }, { label: 'Needs Update', value: '3' }, { label: 'Grade Levels', value: 'Kâ€“12' }, { label: 'Subjects', value: '8' }],
      details: ['24 curriculum maps published to hub', 'Math: Q4 unit progression update needed', 'Science: Lab unit revisions required', 'Language Arts: Reading list additions pending'],
      primaryActionLabel: 'View Curriculum Maps', backActionLabel: 'Resource Hub',
      primaryActionHref: '/curriculum-pd-dashboard', backActionHref: '/curriculum-pd-dashboard', lastUpdated: '8:10 AM' },
    { key: 'resources', icon: 'RS', title: 'Resource Hub', status: 'Current', statusTone: 'good',
      mainKpi: '124 resources published', summary: 'Shared hub current â€” new materials added this week.',
      kpis: [{ label: 'Published', value: '124' }, { label: 'New This Month', value: '8' }, { label: 'Downloads', value: '1,840' }, { label: 'Active Users', value: '42' }],
      details: ['124 curriculum resources in shared hub', '8 new resources published this month', '1,840 total downloads this semester', 'All 42 teachers active users'],
      primaryActionLabel: 'Resource Hub', backActionLabel: 'Add Resource',
      primaryActionHref: '/curriculum-pd-dashboard', backActionHref: '/curriculum-pd-dashboard', lastUpdated: '8:15 AM' },
    { key: 'assessment', icon: 'AS', title: 'Assessment Alignment', status: 'Stable', statusTone: 'good',
      mainKpi: 'Assessments aligned to standards', summary: 'All assessments mapped to learning objectives â€” Q4 review done.',
      kpis: [{ label: 'Assessments Mapped', value: '86' }, { label: 'Standards Aligned', value: '86' }, { label: 'Q4 Review', value: 'Done' }, { label: 'Gaps Found', value: '3' }],
      details: ['86 assessments mapped to standards', '3 alignment gaps identified â€” under revision', 'Q4 alignment review completed', 'Standardized test prep resources published'],
      primaryActionLabel: 'Assessments', backActionLabel: 'Standards Map',
      primaryActionHref: '/curriculum-pd-dashboard', backActionHref: '/curriculum-pd-dashboard', lastUpdated: '8:20 AM' },
    { key: 'summerPD', icon: 'SP', title: 'Summer PD', status: 'Planning', statusTone: 'good',
      mainKpi: 'Retreat July 10â€“11 â€” planning', summary: 'Two-day faculty retreat â€” agenda due June 1.',
      kpis: [{ label: 'Retreat Dates', value: 'Jul 10â€“11' }, { label: 'Agenda Due', value: 'June 1' }, { label: 'Topics Selected', value: '3' }, { label: 'Facilitators', value: '2' }],
      details: ['Summer retreat: July 10â€“11', '3 focus areas selected: AI literacy, Faith Integration, DEI', '2 external facilitators being contracted', 'Agenda draft due to principal June 1'],
      primaryActionLabel: 'Summer PD Planning', backActionLabel: 'View Reports',
      primaryActionHref: '/curriculum-pd-dashboard', backActionHref: '/curriculum-pd-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Faculty PD enrollment', title: 'Teachers in Active PD Tracks', chip: '42 enrolled (100%)', trend: PD_TREND },
    { kicker: 'Observation cycle', title: 'Observations Completed Per Month', chip: '8 remaining', trend: OBS_TREND },
  ],

  activities: [
    '8 classroom observation scheduling requests sent to teachers.',
    'Q4 curriculum map gaps identified â€” Math, Science, ELA updates needed.',
    'Summer PD retreat dates confirmed: July 10â€“11.',
    '8 new resources published to shared curriculum hub.',
    '312 PD hours logged this year â€” 68% of annual target.',
  ],

  quickActions: [
    { label: 'PD Tracks', href: '/curriculum-pd-dashboard' },
    { label: 'Schedule Observations', href: '/curriculum-pd-dashboard' },
    { label: 'Curriculum Maps', href: '/curriculum-pd-dashboard' },
    { label: 'Resource Hub', href: '/curriculum-pd-dashboard' },
  ],

  statuses: [
    { label: 'PD Participation', state: '100% enrolled' },
    { label: 'Observations', state: '8 remaining' },
    { label: 'Curriculum Maps', state: '3 need updates' },
    { label: 'Summer PD', state: 'Planning' },
  ],
};

