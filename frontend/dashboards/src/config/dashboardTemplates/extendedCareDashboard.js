import { LIVE_NOTE } from './_baseData.js';

const ENROLL_TREND = [
  { month: 'Aug', value: 64 }, { month: 'Sep', value: 72 }, { month: 'Oct', value: 74 },
  { month: 'Nov', value: 71 }, { month: 'Dec', value: 68 }, { month: 'Jan', value: 72 },
  { month: 'Feb', value: 74 }, { month: 'Mar', value: 76 },
];
const ATT_TREND = [
  { month: 'Aug', value: 94 }, { month: 'Sep', value: 96 }, { month: 'Oct', value: 95 },
  { month: 'Nov', value: 94 }, { month: 'Dec', value: 93 }, { month: 'Jan', value: 95 },
  { month: 'Feb', value: 96 }, { month: 'Mar', value: 97 },
];

export default {
  key: 'extendedCare',
  activePath: '/extended-care-dashboard',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 2,
  user: { initials: 'EC', name: 'Extended Care Program', role: 'Student Services â€” Before & After School Care' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Extended Care!',
  subtitle: 'Heritage Christian Academy',
  dataState: 'fallback',
  sourceLabel: 'Extended care widgets currently use template snapshots pending live service integration.',
  note: 'Certification remains in review until extended care metrics are sourced from canonical runtime endpoints.',

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/extendedCare/summary/',
  liveDataKey: 'extendedCare',
  metrics: [
    { label: 'Enrolled Students', value: '76', detail: 'Spring semester â€” 44 PM care, 32 AM care.', accent: 'blue' },
    { label: 'Attendance Today', value: '71', detail: '93% rate â€” 5 absent, all families notified.', accent: 'emerald' },
    { label: 'Invoices Due', value: '$4,200', detail: 'April billing â€” 16 families, due April 30.', accent: 'gold' },
    { label: 'Staff Coverage', value: '4/4', detail: 'All 4 staff confirmed â€” 1:19 ratio maintained.', accent: 'navy' },
  ],

  priorities: [
    { title: 'Send April billing reminders', detail: '16 families â€” April invoices due in 8 days.', state: 'Today', tone: 'warn' },
    { title: 'Confirm summer care enrollment', detail: 'Summer registration opens May 1 â€” flyer to families.', state: 'This week', tone: 'nominal' },
    { title: 'Update allergy and medication log', detail: '3 students have updated health forms â€” log needs update.', state: 'Today', tone: 'warn' },
  ],
  prioritiesTitle: 'Extended Care priorities',

  alerts: [
    { title: '3 student health forms updated', detail: 'Allergy and medication logs need updating before tomorrow.', tone: 'warn' },
    { title: 'April invoices due April 30', detail: '$4,200 across 16 families â€” reminders needed today.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'enrollment', icon: 'EN', title: 'Enrollment', status: 'Stable', statusTone: 'good',
      mainKpi: '76 enrolled â€” 44 PM, 32 AM', summary: 'Full capacity at 76 students â€” waiting list active.',
      kpis: [{ label: 'Enrolled', value: '76' }, { label: 'AM Care', value: '32' }, { label: 'PM Care', value: '44' }, { label: 'Waitlist', value: '4' }],
      details: ['76 students enrolled in extended care', '32 in before-school (7â€“8 AM)', '44 in after-school (3â€“5:30 PM)', '4 students on summer waitlist'],
      primaryActionLabel: 'View Roster', backActionLabel: 'Open Enrollment',
      primaryActionHref: '/extended-care-dashboard', backActionHref: '/extended-care-dashboard', lastUpdated: '8:00 AM' },
    { key: 'attendance', icon: 'AT', title: 'Attendance', status: 'Stable', statusTone: 'good',
      mainKpi: '71 present today (93%)', summary: 'High attendance â€” 5 absent families all notified.',
      kpis: [{ label: 'Present', value: '71' }, { label: 'Absent', value: '5' }, { label: 'Rate', value: '93%' }, { label: 'Notified', value: '5/5' }],
      details: ['71 of 76 students present', '5 absences â€” families all notified', 'Check-in complete for AM care', 'Average attendance rate: 97% this semester'],
      primaryActionLabel: 'Attendance Log', backActionLabel: 'Student List',
      primaryActionHref: '/extended-care-dashboard', backActionHref: '/extended-care-dashboard', lastUpdated: '8:10 AM' },
    { key: 'billing', icon: 'BL', title: 'Billing', status: 'Due', statusTone: 'warn',
      mainKpi: '$4,200 due April 30 (16 families)', summary: 'April invoices ready â€” reminders to send today.',
      kpis: [{ label: 'April Amount', value: '$4,200' }, { label: 'Families', value: '16' }, { label: 'Paid Ahead', value: '4' }, { label: 'Due Date', value: 'Apr 30' }],
      details: ['$4,200 in April invoices ready', '16 families billed monthly', '4 families prepaid for semester', 'Reminder emails to send today'],
      primaryActionLabel: 'View Billing', backActionLabel: 'Finance',
      primaryActionHref: '/billing-dashboard', backActionHref: '/finance', lastUpdated: '8:15 AM' },
    { key: 'health', icon: 'HE', title: 'Health & Safety', status: 'Watch', statusTone: 'warn',
      mainKpi: '3 health forms need updating', summary: 'Allergy and medication logs need same-day update.',
      kpis: [{ label: 'Updates Needed', value: '3' }, { label: 'Allergies', value: '8' }, { label: 'Medications', value: '4' }, { label: 'EpiPens', value: '3' }],
      details: ['3 students have updated health forms on file', 'Allergy log must be updated before PM care', '8 students with documented allergies', '3 EpiPens on-site and current'],
      primaryActionLabel: 'Update Health Log', backActionLabel: 'Health Office',
      primaryActionHref: '/health-office-dashboard', backActionHref: '/health-office-dashboard', lastUpdated: '8:20 AM' },
    { key: 'staffing', icon: 'SF', title: 'Staffing', status: 'Full Coverage', statusTone: 'good',
      mainKpi: '4/4 staff confirmed', summary: 'Full coverage â€” 1:19 student-to-staff ratio maintained.',
      kpis: [{ label: 'Staff Today', value: '4' }, { label: 'Required', value: '4' }, { label: 'Ratio', value: '1:19' }, { label: 'Cert. Current', value: 'Yes' }],
      details: ['All 4 extended care staff confirmed', '1:19 student ratio â€” meets state licensing', 'All staff CPR certified and current', 'Substitute available if needed'],
      primaryActionLabel: 'Staff Schedule', backActionLabel: 'HR Dashboard',
      primaryActionHref: '/hr-dashboard', backActionHref: '/hr-dashboard', lastUpdated: '7:55 AM' },
    { key: 'summer', icon: 'SU', title: 'Summer Program', status: 'Planning', statusTone: 'good',
      mainKpi: 'Registration opens May 1', summary: 'Summer care program details ready â€” flyer to families.',
      kpis: [{ label: 'Opens', value: 'May 1' }, { label: 'Capacity', value: '80' }, { label: 'Weeks', value: '10' }, { label: 'Rate', value: '$180/wk' }],
      details: ['Summer care: June 9 â€“ August 14', '10-week program, capacity 80 students', 'Registration flyer ready to send families', 'Early bird discount ends May 15'],
      primaryActionLabel: 'Summer Planning', backActionLabel: 'Communications',
      primaryActionHref: '/communications-dashboard', backActionHref: '/communications-dashboard', lastUpdated: '8:25 AM' },
  ],

  trendPanels: [
    { kicker: 'Program enrollment', title: 'Extended Care Students Enrolled', chip: '76 this semester', trend: ENROLL_TREND },
    { kicker: 'Daily attendance', title: 'Attendance Rate (%)', chip: '97% semester avg', trend: ATT_TREND },
  ],

  activities: [
    'April billing reminders prepared for 16 families.',
    '3 student health forms updated â€” allergy log update needed.',
    'Summer care registration flyer finalized for May 1 send.',
    '5 absences logged today â€” all families notified.',
    'Full staff coverage confirmed for AM and PM sessions.',
  ],

  quickActions: [
    { label: 'Attendance Log', href: '/extended-care-dashboard' },
    { label: 'Send Invoices', href: '/billing-dashboard' },
    { label: 'Health Log', href: '/health-office-dashboard' },
    { label: 'Summer Planning', href: '/extended-care-dashboard' },
  ],

  statuses: [
    { label: 'Enrollment', state: '76 (full)' },
    { label: 'Today Attendance', state: '71/76 (93%)' },
    { label: 'April Billing', state: 'Due April 30' },
    { label: 'Staff Coverage', state: '4/4 confirmed' },
  ],
};

