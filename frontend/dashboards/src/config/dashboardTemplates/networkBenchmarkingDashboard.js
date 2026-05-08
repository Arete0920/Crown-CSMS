import { BASE_NOTE } from './_baseData.js';

const PERF_TREND = [
  { month: 'Aug', value: 72 }, { month: 'Sep', value: 74 }, { month: 'Oct', value: 76 },
  { month: 'Nov', value: 75 }, { month: 'Dec', value: 77 }, { month: 'Jan', value: 78 },
  { month: 'Feb', value: 79 }, { month: 'Mar', value: 81 },
];
const BENCH_TREND = [
  { month: 'Aug', value: 14 }, { month: 'Sep', value: 18 }, { month: 'Oct', value: 22 },
  { month: 'Nov', value: 24 }, { month: 'Dec', value: 26 }, { month: 'Jan', value: 28 },
  { month: 'Feb', value: 30 }, { month: 'Mar', value: 34 },
];

export default {
  key: 'networkBenchmarking',
  activePath: '/network-benchmarking-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'NB', name: 'Network Benchmarking', role: 'Analytics — School Performance & Benchmarking' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Benchmarking Team!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  metrics: [
    { label: 'Schools in Network', value: '47', detail: 'Active schools contributing benchmark data.', accent: 'navy' },
    { label: 'Avg Network Score', value: '81', detail: 'Network average academic performance — up 9 YOY.', accent: 'emerald' },
    { label: 'Benchmarks Met', value: '34', detail: '34 of 48 benchmark indicators met across network.', accent: 'blue' },
    { label: 'Reports Published', value: '6', detail: '6 quarterly benchmark reports this school year.', accent: 'gold' },
  ],

  priorities: [
    { title: 'Publish Q3 benchmark report', detail: 'Data collection closed — report due to network by April 15.', state: 'This week', tone: 'warn' },
    { title: 'Onboard 3 new network schools', detail: 'Jefferson, Covenant, Grace — data entry underway.', state: 'This week', tone: 'nominal' },
    { title: 'Update 14 missing benchmark indicators', detail: '14 of 48 indicators not yet met — identify improvement paths.', state: 'Next month', tone: 'nominal' },
  ],
  prioritiesTitle: 'Benchmarking priorities',

  alerts: [
    { title: 'Q3 benchmark report due April 15', detail: 'Data is ready — final report compilation needed.', tone: 'warn' },
    { title: '14 benchmark indicators not yet met', detail: 'Review lowest-scoring areas and assign improvement plans.', tone: 'nominal' },
  ],

  commandModules: [
    { key: 'network', icon: 'NW', title: 'Network Overview', status: 'Active', statusTone: 'good',
      mainKpi: '47 schools — avg score 81', summary: 'Network growing — 3 schools in onboarding process.',
      kpis: [{ label: 'Schools', value: '47' }, { label: 'Onboarding', value: '3' }, { label: 'Avg Score', value: '81' }, { label: 'YOY Change', value: '+9' }],
      details: ['47 active network schools contributing data', '3 new schools in onboarding: Jefferson, Covenant, Grace', 'Network average score: 81 — up 9 YOY', 'Largest network in diocese history'],
      primaryActionLabel: 'Network Overview', backActionLabel: 'School List',
      primaryActionHref: '/network-benchmarking-dashboard', backActionHref: '/network-benchmarking-dashboard', lastUpdated: '8:00 AM' },
    { key: 'benchmarks', icon: 'BM', title: 'Benchmarks', status: 'Watch', statusTone: 'warn',
      mainKpi: '34/48 benchmarks met', summary: '14 indicators need improvement plans.',
      kpis: [{ label: 'Met', value: '34' }, { label: 'Total', value: '48' }, { label: 'Gap', value: '14' }, { label: 'Categories', value: '6' }],
      details: ['34 of 48 benchmark indicators met', '6 benchmark categories: Academic, Operational, Financial, Compliance, Student Life, Facilities', '14 indicators in improvement process', 'Top performers: Compliance, Financial'],
      primaryActionLabel: 'Benchmark Report', backActionLabel: 'Improvement Plans',
      primaryActionHref: '/network-benchmarking-dashboard', backActionHref: '/network-benchmarking-dashboard', lastUpdated: '8:05 AM' },
    { key: 'performance', icon: 'PF', title: 'Academic Performance', status: 'Trending Up', statusTone: 'good',
      mainKpi: 'Network avg 81 — up 9 points YOY', summary: 'Consistent improvement across all school tiers.',
      kpis: [{ label: 'Network Avg', value: '81' }, { label: 'Top Quartile', value: '≥88' }, { label: 'Heritage Score', value: '84' }, { label: 'Trend', value: '+9 YOY' }],
      details: ['Heritage scores 84 — top quartile in network', 'Network average: 81', 'Bottom quartile: 12 schools below 70', 'Year-over-year improvement: +9 points average'],
      primaryActionLabel: 'Performance Data', backActionLabel: 'School Comparison',
      primaryActionHref: '/network-benchmarking-dashboard', backActionHref: '/network-benchmarking-dashboard', lastUpdated: '8:10 AM' },
    { key: 'reports', icon: 'RP', title: 'Reports', status: 'Due', statusTone: 'warn',
      mainKpi: 'Q3 report due April 15', summary: 'Data compiled — publish by network deadline.',
      kpis: [{ label: 'Reports YTD', value: '6' }, { label: 'Q3 Due', value: 'Apr 15' }, { label: 'Data Ready', value: 'Yes' }, { label: 'Format', value: 'PDF + Dashboard' }],
      details: ['Q3 benchmark report due April 15', 'All 47 schools submitted Q3 data', 'PDF summary + interactive dashboard required', 'Distribution: 47 school principals + diocese'],
      primaryActionLabel: 'Publish Report', backActionLabel: 'View History',
      primaryActionHref: '/network-benchmarking-dashboard', backActionHref: '/network-benchmarking-dashboard', lastUpdated: '8:15 AM' },
    { key: 'onboarding', icon: 'OB', title: 'School Onboarding', status: 'In Progress', statusTone: 'good',
      mainKpi: '3 schools in onboarding', summary: 'Jefferson, Covenant, Grace — data setup underway.',
      kpis: [{ label: 'Onboarding', value: '3' }, { label: 'Data Received', value: '2/3' }, { label: 'Target Live', value: 'May 1' }, { label: 'Onboarded YTD', value: '4' }],
      details: ['3 schools in onboarding pipeline', 'Jefferson: data received — mapping in progress', 'Covenant: data received — mapping in progress', 'Grace: data entry pending'],
      primaryActionLabel: 'Onboarding Status', backActionLabel: 'School Setup',
      primaryActionHref: '/network-benchmarking-dashboard', backActionHref: '/implementation-success-dashboard', lastUpdated: '8:20 AM' },
    { key: 'trends', icon: 'TR', title: 'Network Trends', status: 'Positive', statusTone: 'good',
      mainKpi: 'Consistent upward trend — all categories', summary: 'Year-over-year growth across all benchmark categories.',
      kpis: [{ label: 'Overall', value: '+9 YOY' }, { label: 'Academic', value: '+11' }, { label: 'Operational', value: '+6' }, { label: 'Financial', value: '+4' }],
      details: ['Academic: +11 points year-over-year', 'Operational: +6 points', 'Financial: +4 points', 'Student Life: +8 points'],
      primaryActionLabel: 'Trend Analysis', backActionLabel: 'Historical Data',
      primaryActionHref: '/network-benchmarking-dashboard', backActionHref: '/network-benchmarking-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Network performance', title: 'Avg Network Academic Score', chip: '81 (Q3)', trend: PERF_TREND },
    { kicker: 'Benchmark progress', title: 'Cumulative Benchmarks Met', chip: '34/48 met', trend: BENCH_TREND },
  ],

  activities: [
    'Q3 benchmark data compiled — report drafting in progress for April 15.',
    'Jefferson and Covenant school data mapped — Grace pending.',
    'Heritage scores 84 — top quartile in network.',
    '14 improvement plans identified for unmet benchmarks.',
    'Network size confirmed at 47 schools — largest on record.',
  ],

  quickActions: [
    { label: 'Benchmark Report', href: '/network-benchmarking-dashboard' },
    { label: 'Network Overview', href: '/network-benchmarking-dashboard' },
    { label: 'School Onboarding', href: '/implementation-success-dashboard' },
    { label: 'Performance Data', href: '/network-benchmarking-dashboard' },
  ],

  statuses: [
    { label: 'Network Schools', state: '47 active' },
    { label: 'Benchmarks', state: '34/48 met' },
    { label: 'Q3 Report', state: 'Due April 15' },
    { label: 'New Schools', state: '3 onboarding' },
  ],
};
