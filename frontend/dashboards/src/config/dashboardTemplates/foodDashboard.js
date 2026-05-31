import { BASE_NOTE } from './_baseData.js';

const MEALS_TREND = [
  { month: 'Sep', value: 268 }, { month: 'Oct', value: 274 }, { month: 'Nov', value: 281 },
  { month: 'Dec', value: 270 }, { month: 'Jan', value: 285 }, { month: 'Feb', value: 287 }, { month: 'Mar', value: 290 },
];
const REVENUE_TREND = [
  { month: 'Sep', value: 980 }, { month: 'Oct', value: 1080 }, { month: 'Nov', value: 1140 },
  { month: 'Dec', value: 1100 }, { month: 'Jan', value: 1180 }, { month: 'Feb', value: 1230 }, { month: 'Mar', value: 1248 },
];

export default {
  key: 'food',
  activePath: '/food',
  schoolName: 'Heritage Christian Academy',
  updatesCount: 4,
  user: { initials: 'FS', name: 'Food Services', role: 'Food Services â€” Meals & Inventory' },
  eyebrow: 'CROWN Launch Preview',
  title: 'Good morning, Food Services!',
  subtitle: 'Heritage Christian Academy',
  note: BASE_NOTE,

  dataSource: 'live_api',
  apiEndpoint: '/api/v1/dashboards/food/summary/',
  liveDataKey: 'food',
  metrics: [
    { label: 'Meals Served Today', value: '287', detail: 'Above 4-day average â€” supply on hand sufficient.', accent: 'emerald' },
    { label: 'Free / Reduced Count', value: '62', detail: '28% of total meals â€” within program plan.', accent: 'navy' },
    { label: 'Inventory Low Items', value: '4', detail: 'Reorder list ready for office approval.', accent: 'gold' },
    { label: 'Payments Pending', value: '18', detail: '$1,248 collected MTD across active accounts.', accent: 'gold' },
  ],

  priorities: [
    { title: 'Approve reorder for 4 low items', detail: 'Buns, milk, apple sauce cups, and gloves running low.', state: 'Today', tone: 'warn' },
    { title: 'Follow up on 18 pending payments', detail: 'Send balance reminders to families with low accounts.', state: 'This week', tone: 'warn' },
    { title: 'Confirm tomorrow\u2019s menu prep', detail: 'Beef tacos and corn on the schedule for Friday.', state: 'Today', tone: 'warn' },
  ],
  prioritiesTitle: 'Food services priorities',

  alerts: [
    { title: '4 inventory items low', detail: 'Order before Friday to prevent menu substitution.', tone: 'warn' },
    { title: '12 low-balance alerts', detail: 'Family balance reminders going out this week.', tone: 'warn' },
  ],

  commandModules: [
    { key: 'meals', icon: 'ML', title: 'Meals Served', status: 'Stable', statusTone: 'good',
      mainKpi: '287 meals today', summary: 'Service running on plan â€” afternoon counts below capacity.',
      kpis: [{ label: 'Today', value: '287' }, { label: '4-day avg', value: '283' }, { label: 'F/R %', value: '28%' }, { label: 'Capacity', value: '320' }],
      details: ['287 meals served today across all sittings', '4-day moving average at 283', 'Free/reduced participation at 28%', 'Capacity headroom: 33 meals'],
      primaryActionLabel: 'Open Meal Log', backActionLabel: 'Service Reports',
      primaryActionHref: '/food', backActionHref: '/reports', lastUpdated: '8:30 AM' },
    { key: 'menu', icon: 'MN', title: 'Menu', status: 'Stable', statusTone: 'good',
      mainKpi: 'Today: Grilled Chicken Sandwich', summary: 'Today and tomorrow menus published. Substitutions logged.',
      kpis: [{ label: 'Today entree', value: 'Chicken' }, { label: 'Today side', value: 'Caesar' }, { label: 'Tomorrow entree', value: 'Tacos' }, { label: 'Substitutions', value: '0' }],
      details: ['Today: Grilled Chicken Sandwich, Caesar Salad', 'Today: Apple Slices, Chocolate Milk', 'Tomorrow: Beef Tacos, Corn', 'Tomorrow: Orange Wedges, 2% White Milk'],
      primaryActionLabel: 'Open Menu Planner', backActionLabel: 'Substitutions',
      primaryActionHref: '/food', backActionHref: '/food', lastUpdated: '8:15 AM' },
    { key: 'inventory', icon: 'IN', title: 'Inventory', status: 'Watch', statusTone: 'warn',
      mainKpi: '4 items low', summary: 'Whole wheat buns, chocolate milk, apple sauce cups, latex gloves.',
      kpis: [{ label: 'Low items', value: '4' }, { label: 'Out of stock', value: '0' }, { label: 'Reorder draft', value: 'Ready' }, { label: 'Vendor count', value: '3' }],
      details: ['Whole wheat buns â€” low', 'Chocolate milk â€” low', 'Apple sauce cups â€” low', 'Latex gloves (M) â€” low'],
      primaryActionLabel: 'Open Inventory', backActionLabel: 'Reorder Draft',
      primaryActionHref: '/food', backActionHref: '/finance', lastUpdated: '8:00 AM' },
    { key: 'payments', icon: 'PY', title: 'Payments & Accounts', status: 'Watch', statusTone: 'warn',
      mainKpi: '$1,248 MTD / 18 pending', summary: 'Collections on plan â€” 12 low-balance reminders going out.',
      kpis: [{ label: 'Revenue MTD', value: '$1,248' }, { label: 'Pending payments', value: '18' }, { label: 'Low balance', value: '12' }, { label: 'F/R enrolled', value: '62' }],
      details: ['$1,248 collected month to date', '18 payments pending across active accounts', '12 family low-balance reminders queued', '62 students enrolled in free/reduced program'],
      primaryActionLabel: 'Open Payment Console', backActionLabel: 'Family Statements',
      primaryActionHref: '/finance', backActionHref: '/communications', lastUpdated: '7:50 AM' },
    { key: 'compliance', icon: 'CM', title: 'Health & Compliance', status: 'Stable', statusTone: 'good',
      mainKpi: 'All checks current', summary: 'Health inspection log current; allergen plan documented.',
      kpis: [{ label: 'Last inspection', value: 'Feb 4' }, { label: 'Open findings', value: '0' }, { label: 'Allergen flags', value: '4' }, { label: 'Staff training', value: 'Current' }],
      details: ['Last health inspection Feb 4 â€” no findings', 'Allergen flags tracked for 4 students', 'Staff food handling training current', 'Quarterly allergen audit on schedule'],
      primaryActionLabel: 'Compliance Console', backActionLabel: 'Allergen Records',
      primaryActionHref: '/food', backActionHref: '/health', lastUpdated: '7:35 AM' },
    { key: 'communications', icon: 'CO', title: 'Family Communications', status: 'Stable', statusTone: 'good',
      mainKpi: 'Menu sent Mon / balances Wed', summary: 'Menus and balance notices delivered on schedule.',
      kpis: [{ label: 'Menus sent', value: '1' }, { label: 'Balance notices', value: '12' }, { label: 'Survey replies', value: '38' }, { label: 'Allergen letters', value: '2' }],
      details: ['Weekly menu sent Monday', '12 balance notices going out Wednesday', '38 family survey replies received', '2 allergen letters mailed this week'],
      primaryActionLabel: 'Open Communications', backActionLabel: 'Notice Library',
      primaryActionHref: '/communications', backActionHref: '/food', lastUpdated: '7:20 AM' },
  ],

  trendPanels: [
    { kicker: 'Meals trend', title: 'Average daily meals served by month', chip: 'Steady', trend: MEALS_TREND },
    { kicker: 'Revenue trend', title: 'Monthly meal revenue ($)', chip: '+15% YoY', trend: REVENUE_TREND },
  ],

  activityKicker: 'Food services activity',
  activityTitle: 'Recent food services events',
  activities: [
    '287 meals served at lunch service today.',
    'Reorder draft prepared for 4 low inventory items.',
    'Allergen letters mailed to 2 families.',
    '12 low-balance reminders queued for Wednesday.',
    'Menu published for the upcoming week.',
  ],

  quickActions: [
    { title: 'Open Finance', eyebrow: 'Quick action', description: 'Manage meal payments and family balances.', actionLabel: 'Open Finance', href: '/finance', allowedRoles: ['food'] },
    { title: 'Open Health', eyebrow: 'Quick action', description: 'Coordinate allergen plans with the nurse.', actionLabel: 'Open Health', href: '/health', allowedRoles: ['food'] },
    { title: 'Communications', eyebrow: 'Quick action', description: 'Send menu and balance notices to families.', actionLabel: 'Open Communications', href: '/communications', allowedRoles: ['food'] },
    { title: 'Open Food Services', eyebrow: 'Quick action', description: 'Return to the Food Services command center.', actionLabel: 'Open Food Services', href: '/food', allowedRoles: ['food'] },
  ],

  statusTitle: 'Food Services workspace status',
  statusKicker: 'System health',
  statuses: [
    { label: 'Meal Counts', state: 'Synced' },
    { label: 'Inventory', state: '4 low' },
    { label: 'Payments', state: 'On track' },
    { label: 'Compliance', state: 'Current' },
  ],
};

