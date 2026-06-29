function identityTransform(response) {
  return response;
}

function createDataConfig(endpoint, options = {}) {
  return {
    endpoint,
    method: options.method || 'GET',
    query: options.query || undefined,
    allowScaffoldFallback: options.allowScaffoldFallback ?? false,
    fallbackData: options.fallbackData ?? null,
    transform: options.transform || identityTransform,
  };
}

function dashboardSummaryPath(slug) {
  return `/api/v1/dashboards/${slug}/summary`;
}

export const DEMO_CRITICAL_DASHBOARD_KEYS = Object.freeze([
  'school-administrator',
  'admissions',
  'registrar',
  'billing',
  'financial-aid',
  'attendance',
  'gradebook',
  'communications',
  'scheduling',
  'parent',
  'teacher',
  'student',
  'dashboard-certification-center',
  'release-reliability',
  'compliance-audit',
]);

function createDemoCriticalFallback(dashboardKey, label, options = {}) {
  return {
    dashboard_key: dashboardKey,
    metrics: options.metrics ?? [
      { label: 'Live Data Certification', value: 'Pending' },
      { label: 'Demo Data State', value: 'Fallback' },
      { label: 'Permission Proof', value: 'Required' },
      { label: 'Tenant Proof', value: 'Required' },
    ],
    alerts: options.alerts ?? [
      {
        title: `${label} dashboard is using disclosed fallback data`,
        level: 'Medium',
        secondary: 'This is a sandbox/demo truth state. Live-data certification requires API, permission, tenant, runtime, and evidence proof before promotion.',
      },
    ],
    queue: options.queue ?? [
      `Wire ${label} live summary service`,
      `Attach ${label} KPI/data provenance evidence`,
      `Prove ${label} permission and tenant boundaries`,
      `Capture ${label} browser proof and screenshot/trace`,
    ],
    meta: {
      fallback_source: 'frontend_demo_truth_guard',
      ...options.meta,
      served_from: options.servedFrom || 'fallback',
      certification_candidate: 'demo-critical',
      live_certified: false,
      sandbox_demo_only: true,
    },
  };
}

function createDemoCriticalDataConfig(slug, label, options = {}) {
  return createDataConfig(dashboardSummaryPath(slug), {
    ...options,
    allowScaffoldFallback: true,
    fallbackData: options.fallbackData ?? createDemoCriticalFallback(slug, label, options),
  });
}

export const DASHBOARD_DATA_REGISTRY = {
  // Tier 1
  attendance: createDemoCriticalDataConfig('attendance', 'Attendance', {
    fallbackData: createDemoCriticalFallback('attendance', 'Attendance', {
      servedFrom: 'sample',
      metrics: [
        { label: 'Present Rate Today', value: '96.1%' },
        { label: 'Absent Students', value: '14' },
        { label: 'Late Check-Ins', value: '9' },
        { label: 'Missing Homerooms', value: '3' },
      ],
      alerts: [
        {
          title: 'Three homerooms still need final attendance submission',
          level: 'High',
          secondary: 'Attendance office follow-up required. Sample state is explicitly disclosed for sandbox/demo use.',
        },
        {
          title: 'Grade 10 absentee trend is above weekly threshold',
          level: 'Medium',
          secondary: 'Review with school admin and student care. Sample state is explicitly disclosed for sandbox/demo use.',
        },
        {
          title: 'Two parent outreach messages bounced',
          level: 'Low',
          secondary: 'Retry communication workflow. Sample state is explicitly disclosed for sandbox/demo use.',
        },
      ],
      queue: [
        'Review unsubmitted homeroom attendance',
        'Send parent outreach for chronic absence group',
        'Confirm late-check-in corrections from front office',
        'Publish attendance exception summary',
      ],
      meta: {
        documented_exception: 'sandbox_demo_sample_only',
      },
    }),
  }),
  billing: createDemoCriticalDataConfig('billing', 'Billing'),
  'financial-aid': createDemoCriticalDataConfig('financial-aid', 'Financial Aid'),
  registrar: createDemoCriticalDataConfig('registrar', 'Registrar'),

  // Tier 2
  scheduling: createDemoCriticalDataConfig('scheduling', 'Scheduling'),
  gradebook: createDemoCriticalDataConfig('gradebook', 'Gradebook'),
  'student-care': createDataConfig(dashboardSummaryPath('student-care')),
  'activities-athletics': createDataConfig(dashboardSummaryPath('activities-athletics')),
  communications: createDemoCriticalDataConfig('communications', 'Communications'),

  // Tier 3
  'school-administrator': createDemoCriticalDataConfig('school-administrator', 'School Administrator'),
  'school-board': createDataConfig(dashboardSummaryPath('school-board')),
  'master-control': createDataConfig(dashboardSummaryPath('master-control')),
  admissions: createDemoCriticalDataConfig('admissions', 'Admissions'),
  advancement: createDataConfig(dashboardSummaryPath('advancement')),

  // Sandbox/demo persona dashboards
  parent: createDemoCriticalDataConfig('parent', 'Parent'),
  teacher: createDemoCriticalDataConfig('teacher', 'Teacher'),
  student: createDemoCriticalDataConfig('student', 'Student'),

  // Tier 4
  hr: createDataConfig(dashboardSummaryPath('hr')),
  facilities: createDataConfig(dashboardSummaryPath('facilities')),
  'health-office': createDataConfig(dashboardSummaryPath('health-office')),
  transportation: createDataConfig(dashboardSummaryPath('transportation')),
  'food-service': createDataConfig(dashboardSummaryPath('food-service')),
  'it-support': createDataConfig(dashboardSummaryPath('it-support')),

  // Tier 5
  'fine-arts': createDataConfig(dashboardSummaryPath('fine-arts')),
  'athletics-director': createDataConfig(dashboardSummaryPath('athletics-director')),
  'library-media': createDataConfig(dashboardSummaryPath('library-media')),
  'extended-care': createDataConfig(dashboardSummaryPath('extended-care')),
  'summer-camp': createDataConfig(dashboardSummaryPath('summer-camp')),
  'safety-security': createDataConfig(dashboardSummaryPath('safety-security')),
  'curriculum-pd': createDataConfig(dashboardSummaryPath('curriculum-pd')),

  // Tier 6
  'chaplain-spiritual-life': createDataConfig(dashboardSummaryPath('chaplain-spiritual-life')),
  'advancement-operations': createDataConfig(dashboardSummaryPath('advancement-operations')),
  'volunteer-management': createDataConfig(dashboardSummaryPath('volunteer-management')),
  'portrait-service': createDataConfig(dashboardSummaryPath('portrait-service')),
  'alumni-relations': createDataConfig(dashboardSummaryPath('alumni-relations')),
  'network-benchmarking': createDataConfig(dashboardSummaryPath('network-benchmarking')),

  // Tier 7
  'implementation-success': createDataConfig(dashboardSummaryPath('implementation-success')),
  'data-migration': createDataConfig(dashboardSummaryPath('data-migration')),
  'integrations-automation': createDataConfig(dashboardSummaryPath('integrations-automation')),
  'compliance-audit': createDemoCriticalDataConfig('compliance-audit', 'Compliance / Audit', {
    fallbackData: createDemoCriticalFallback('compliance-audit', 'Compliance / Audit', {
      metrics: [
        { label: 'Active Audit Proof Streams', value: 'TBD' },
        { label: 'Controls Passing', value: 'TBD' },
        { label: 'Open Findings', value: 'TBD' },
        { label: 'Reviews Due (30d)', value: 'TBD' },
      ],
      alerts: [
        {
          title: 'Compliance dashboard is using fallback proof data',
          level: 'Medium',
          secondary: 'Replace the sample-backed summary service with a certified live compliance truth source before promotion.',
        },
        {
          title: 'Owner and independent reviewer are still TBD',
          level: 'High',
          secondary: 'Assign governance roles before promotion beyond API_WIRED.',
        },
      ],
      queue: [
        'Assign compliance dashboard owner',
        'Assign independent compliance reviewer',
        'Replace the sample-backed compliance summary service',
        'Attach permission, tenant, and browser proof',
      ],
      meta: {
        fallback_source: 'frontend_scaffold',
      },
    }),
  }),
  'revenue-operations': createDataConfig(dashboardSummaryPath('revenue-operations')),
  'release-reliability': createDemoCriticalDataConfig('release-reliability', 'Release Reliability', {
    fallbackData: createDemoCriticalFallback('release-reliability', 'Release Reliability', {
      metrics: [
        { label: 'Deployments This Month', value: '9' },
        { label: 'Open Production Incidents', value: '2' },
        { label: 'Failed Checks in Last 24h', value: '4' },
        { label: 'Release Readiness', value: 'Watch' },
      ],
      alerts: [
        {
          title: 'Contract gate failed on last main candidate build',
          level: 'High',
          secondary: 'Platform engineering follow-up required. Fallback state is explicitly disclosed.',
        },
        {
          title: 'Two environments are not on expected build SHA',
          level: 'High',
          secondary: 'Verify deployment alignment. Fallback state is explicitly disclosed.',
        },
        {
          title: 'Release proof packet is incomplete for one deploy',
          level: 'Medium',
          secondary: 'Complete evidence before certification. Fallback state is explicitly disclosed.',
        },
      ],
      queue: [
        'Review failed release gate evidence',
        'Verify environment build SHA alignment',
        'Close open production incident postmortem tasks',
        'Publish release readiness summary',
      ],
      meta: {
        fallback_source: 'frontend_scaffold',
      },
    }),
  }),

  // Phase 9 control page
  'dashboard-certification-center': createDemoCriticalDataConfig('dashboard-certification-center', 'Dashboard Certification Center', {
    fallbackData: createDemoCriticalFallback('dashboard-certification-center', 'Dashboard Certification Center', {
      metrics: [
        { label: 'Dashboards Certified', value: '0' },
        { label: 'Mapped Only', value: '40' },
        { label: 'Pending Independent Review', value: '0' },
        { label: 'Cert Rate', value: '0%' },
      ],
      alerts: [
        {
          title: 'No dashboards are certified yet',
          level: 'High',
          secondary: 'Current verified state remains 40 mapped dashboards and 0 live-data certified dashboards.',
        },
        {
          title: 'Owner and independent reviewer are still TBD',
          level: 'High',
          secondary: 'Assign governance roles before certification promotion.',
        },
      ],
      queue: [
        'Assign dashboard certification owner',
        'Assign independent dashboard certification reviewer',
        'Wire certification proof state from the dashboard matrix',
        'Attach permission, tenant, and runtime proof',
      ],
      meta: {
        fallback_source: 'frontend_scaffold',
      },
    }),
  }),
};