export const BASE_TREND = [
  { month: 'Sep', value: 1184 },
  { month: 'Oct', value: 1198 },
  { month: 'Nov', value: 1216 },
  { month: 'Dec', value: 1228 },
  { month: 'Jan', value: 1236 },
  { month: 'Feb', value: 1241 },
  { month: 'Mar', value: 1248 },
];

export const LIVE_NOTE = 'Widget badges disclose data provenance and non-live states.';

export const BASE_NOTE = 'Sandbox preview data shown. Connect backend for live records.';

export const BASE_COMMUNICATIONS = {
  inboxTitle: 'Unread and waiting',
  inboxSummary: 'Communications remains a shared operating spine across family, teacher, and school workflows.',
  inboxItems: [
    '3 family replies still need response.',
    '1 teacher follow-up is due before noon.',
    'Weekly bulletin draft is waiting for review.',
  ],
  inboxActionLabel: 'Open Inbox',
  inboxActionHref: '/communications',
  announcementsTitle: 'Announcements and bulletin',
  announcementsSummary: 'Shared notices, reminders, and publication queue status.',
  announcementItems: [
    'Thursday parent bulletin scheduled for 3:00 PM.',
    'Chapel reminder is queued for tomorrow morning.',
    'Field trip permission note remains pinned for families.',
  ],
  announcementsActionLabel: 'View Announcements',
  announcementsActionHref: '/communications',
  urgentTitle: 'Alerts and escalations',
  urgentSummary: 'Urgent communication risk and unresolved delivery items.',
  urgentItems: [
    'No emergency alerts active.',
    'Message delivery queue healthy.',
    'Translation backlog cleared for the current cycle.',
  ],
  urgentActionLabel: 'Review Alerts',
  urgentActionHref: '/communications',
};

export const BASE_ACTIVITY = [
  'Registrar verified reenrollment packets before chapel.',
  'Finance posted tuition receipts for the April billing cycle.',
  'Admissions scheduled new parent tours for next week.',
  'IT closed classroom device tickets before first period.',
];

export const BASE_STATUS = [
  { label: 'SIS Sync', state: 'Healthy' },
  { label: 'Attendance Upload', state: 'On schedule' },
  { label: 'Family Billing', state: 'Ready' },
  { label: 'Staff Workflows', state: 'Stable' },
];

export const BASE_OPERATIONS = [
  { area: 'Enrollment', owner: 'Admissions', status: 'Applications reviewed', updated: '8:10 AM' },
  { area: 'Attendance', owner: 'Student Life', status: 'Homeroom sync complete', updated: '8:22 AM' },
  { area: 'Finance', owner: 'Business Office', status: 'Deposit batch posted', updated: '8:35 AM' },
  { area: 'Communications', owner: 'Front Office', status: 'Parent bulletin queued', updated: '8:42 AM' },
];

export const BASE_FAITH_COMMUNITY = {
  devotion: {
    scripture: '"Trust in the Lord with all your heart and lean not on your own understanding."',
    reference: 'Proverbs 3:5',
    reflection: 'Leadership in Christian education begins with humility before God. Every decision shapes the lives of students entrusted to us.',
    actionLabel: 'Read More',
    actionHref: 'https://www.biblegateway.com/passage/?search=Proverbs%203%3A5&version=KJV',
  },
  prayerActionHref: '/spiritual-life',
  announcementsActionHref: '/communications',
  celebrationsActionHref: '/spiritual-life',
  prayerRequests: [
    'Mrs. Carter surgery recovery',
    'Wisdom for leadership meetings',
    '6th grade retreat travel safety',
    'New families joining this week',
  ],
  announcements: [
    'Chapel Friday at 9:00 AM',
    'Re-enrollment packets due Monday',
    'Parent newsletter scheduled for Thursday',
    'Uniform order deadline approaching',
  ],
  celebrations: [
    { name: 'Mr. Thompson', reason: '20-year anniversary at Heritage', tone: 'gold' },
    { name: 'Sarah M., Grade 8', reason: 'State science fair finalist', tone: 'good' },
    { name: 'Robotics Team', reason: 'Regional championship win', tone: 'good' },
    { name: 'Mrs. Chen', reason: 'New baby — Elijah born this week', tone: 'gold' },
  ],
};
