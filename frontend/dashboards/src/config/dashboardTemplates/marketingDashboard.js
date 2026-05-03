import { BASE_NOTE } from './_baseData.js';

const INQUIRY_TREND = [
  { month: 'Sep', value: 18 }, { month: 'Oct', value: 22 }, { month: 'Nov', value: 20 },
  { month: 'Dec', value: 24 }, { month: 'Jan', value: 26 }, { month: 'Feb', value: 28 }, { month: 'Mar', value: 31 },
];
const FUNNEL_TREND = [
  { month: 'Sep', value: 62 }, { month: 'Oct', value: 71 }, { month: 'Nov', value: 79 },
  { month: 'Dec', value: 96 }, { month: 'Jan', value: 124 }, { month: 'Feb', value: 158 }, { month: 'Mar', value: 187 },
];

export default {
  key: 'marketing',
  activePath: '/marketing',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'MA', name: 'Marketing & Advancement', role: 'Marketing — Funnel & Campaigns' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Marketing!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  metrics: [
    { label: 'Inquiries YTD', value: '187', detail: '+24% vs prior year — pipeline strong.', accent: 'blue' },
    { label: 'Tours Scheduled', value: '62', detail: 'Open House tours filling at 90% capacity.', accent: 'gold' },
    { label: 'Applications', value: '54', detail: '38 enrolled to date, 16 awaiting decision.', accent: 'navy' },
    { label: 'Stalled Leads', value: '11', detail: 'No follow-up >7 days — re-engagement queue active.', accent: 'gold' },
  ],

  priorities: [
    { title: 'Re-engage 11 stalled leads', detail: 'No follow-up >7 days — assign to admissions counselor.', state: 'Today', tone: 'warn' },
    { title: 'Boost Open House RSVPs', detail: 'Currently 28 of 50 target — push email + social cadence.', state: 'This week', tone: 'warn' },
    { title: 'Finalize spring digital ad refresh', detail: 'Q1 creative ends Friday — Q2 assets in review.', state: 'This week', tone: 'warn' },
  ],
  prioritiesTitle: 'Marketing priorities',

  alerts: [
    { title: '11 leads with no follow-up >7 days', detail: 'SLA breach — escalation queue active for re-assignment.', tone: 'warn' },
    { title: 'Open House RSVPs below target', detail: '28 of 50 target — additional outreach this week.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'funnel', icon: 'FN', title: 'Enrollment Funnel', status: 'Stable', statusTone: 'good',
      mainKpi: '187 → 62 → 54 → 38', summary: 'Funnel conversion holding above last year at every stage.',
      kpis: [{ label: 'Inquiries', value: '187' }, { label: 'Tours', value: '62' }, { label: 'Applied', value: '54' }, { label: 'Enrolled', value: '38' }],
      details: ['Inquiry → tour conversion 33%', 'Tour → application conversion 87%', 'Application → enrolled conversion 70%', 'Overall yield: 20% inquiry-to-enrolled'],
      primaryActionLabel: 'Open Admissions', backActionLabel: 'View Pipeline',
      primaryActionHref: '/admissions', backActionHref: '/admissions/pipeline', lastUpdated: '8:30 AM' },
    { key: 'campaigns', icon: 'CP', title: 'Campaigns', status: 'Stable', statusTone: 'good',
      mainKpi: '2 active / 1 complete', summary: 'Campaign portfolio delivering 28 conversions this quarter.',
      kpis: [{ label: 'Active campaigns', value: '2' }, { label: 'Completed', value: '1' }, { label: 'Total leads', value: '87' }, { label: 'Total conversions', value: '28' }],
      details: ['Spring Open House: 28 leads / 9 conversions', 'Digital Ads Q1: 41 leads / 12 conversions', 'Referral Drive complete: 18 leads / 7 conversions', 'Q2 creative refresh in progress'],
      primaryActionLabel: 'Open Campaigns', backActionLabel: 'Performance Report',
      primaryActionHref: '/marketing', backActionHref: '/reports', lastUpdated: '8:15 AM' },
    { key: 'sources', icon: 'SR', title: 'Lead Sources', status: 'Stable', statusTone: 'good',
      mainKpi: 'Website 40% / Referral 30%', summary: 'Source mix balanced across web, referral, social, and event.',
      kpis: [{ label: 'Website', value: '74' }, { label: 'Referral', value: '56' }, { label: 'Social', value: '37' }, { label: 'Event', value: '20' }],
      details: ['Website inquiries leading at 40% share', 'Referral channel growing 12% YoY', 'Social inquiries up after Q1 ad push', 'Event source reflects Open House traffic'],
      primaryActionLabel: 'Open Source Report', backActionLabel: 'Channel Detail',
      primaryActionHref: '/marketing', backActionHref: '/reports', lastUpdated: '8:00 AM' },
    { key: 'engagement', icon: 'EN', title: 'Digital Engagement', status: 'Stable', statusTone: 'good',
      mainKpi: '1,842 web visits / 42% email open', summary: 'Web and email engagement up vs last month.',
      kpis: [{ label: 'Web visits MTD', value: '1,842' }, { label: 'Email open rate', value: '42%' }, { label: 'Social followers', value: '2,140' }, { label: 'Avg session', value: '2:14' }],
      details: ['Web visits +14% vs last month', 'Email open rate +3% vs last month', 'Social followers +32 this month', 'Top page: Open House landing'],
      primaryActionLabel: 'Open Analytics', backActionLabel: 'Email Reports',
      primaryActionHref: '/marketing', backActionHref: '/communications', lastUpdated: '7:50 AM' },
    { key: 'open-house', icon: 'OH', title: 'Open House', status: 'Watch', statusTone: 'warn',
      mainKpi: '28 of 50 RSVPs', summary: 'RSVPs below target — push outreach this week.',
      kpis: [{ label: 'RSVPs', value: '28' }, { label: 'Target', value: '50' }, { label: 'Capacity', value: '60%' }, { label: 'Tour slots open', value: '12' }],
      details: ['RSVPs at 56% of target with 10 days left', 'Tour slot capacity 60% reserved', 'Email reminder scheduled Wednesday', 'Social push planned Thursday and Friday'],
      primaryActionLabel: 'Open House Console', backActionLabel: 'View RSVPs',
      primaryActionHref: '/marketing', backActionHref: '/admissions', lastUpdated: '7:40 AM' },
    { key: 'communications', icon: 'CO', title: 'Marketing Communications', status: 'Stable', statusTone: 'good',
      mainKpi: 'Newsletter sent Mon / 2 social posts', summary: 'Weekly cadence on schedule across all channels.',
      kpis: [{ label: 'Newsletters sent', value: '4' }, { label: 'Social posts week', value: '6' }, { label: 'Press inquiries', value: '0' }, { label: 'Pending content', value: '2' }],
      details: ['Family newsletter delivered Monday', '6 social posts published this week', 'Q2 ad creative in legal review', 'Spring gala save-the-date in progress'],
      primaryActionLabel: 'Open Communications', backActionLabel: 'Content Queue',
      primaryActionHref: '/communications', backActionHref: '/marketing', lastUpdated: '7:30 AM' },
  ],

  trendPanels: [
    { kicker: 'Inquiry trend', title: 'New inquiries by month', chip: 'Above prior year', trend: INQUIRY_TREND },
    { kicker: 'Cumulative funnel', title: 'YTD inquiries cumulative', chip: '+24% YoY', trend: FUNNEL_TREND },
  ],

  activityKicker: 'Marketing activity',
  activityTitle: 'Recent marketing events',
  activities: [
    'Spring Open House landing page published.',
    'Digital Ads Q1 campaign generated 12 conversions.',
    'Referral Drive campaign closed at 7 conversions.',
    'Family newsletter delivered to 412 households.',
    '6 social posts scheduled for the week.',
  ],

  quickActions: [
    { title: 'Open Admissions', eyebrow: 'Quick action', description: 'View admissions pipeline and conversion data.', actionLabel: 'Open Admissions', href: '/admissions', allowedRoles: ['marketing'] },
    { title: 'Communications', eyebrow: 'Quick action', description: 'Send family newsletter and campaign emails.', actionLabel: 'Open Communications', href: '/communications', allowedRoles: ['marketing'] },
    { title: 'Reports', eyebrow: 'Quick action', description: 'Review campaign and channel performance reports.', actionLabel: 'Open Reports', href: '/reports', allowedRoles: ['marketing'] },
    { title: 'Campaigns', eyebrow: 'Quick action', description: 'Manage active campaigns and creative refresh.', actionLabel: 'Open Campaigns', href: '/marketing', allowedRoles: ['marketing'] },
  ],

  statusTitle: 'Marketing workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'CRM Pipeline', state: 'Synced' },
    { label: 'Email Platform', state: 'Online' },
    { label: 'Analytics', state: 'Tracking' },
    { label: 'Social Channels', state: 'Active' },
  ],
};
