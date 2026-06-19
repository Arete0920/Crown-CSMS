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

export const DASHBOARD_DATA_REGISTRY = {
  // Tier 1
  attendance: createDataConfig(dashboardSummaryPath('attendance'), {
    allowScaffoldFallback: true,
    fallbackData: {
      dashboard_key: 'attendance',
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
          secondary: 'Attendance office follow-up required.',
        },
        {
          title: 'Grade 10 absentee trend is above weekly threshold',
          level: 'Medium',
          secondary: 'Review with school admin and student care.',
        },
        {
          title: 'Two parent outreach messages bounced',
          level: 'Low',
          secondary: 'Retry communication workflow.',
        },
      ],
      queue: [
        'Review unsubmitted homeroom attendance',
        'Send parent outreach for chronic absence group',
        'Confirm late-check-in corrections from front office',
        'Publish attendance exception summary',
      ],
      meta: {
        served_from: 'sample',
        certification_candidate: 'hybrid',
      },
    },
  }),
  billing: createDataConfig(dashboardSummaryPath('billing')),
  'financial-aid': createDataConfig(dashboardSummaryPath('financial-aid')),
  registrar: createDataConfig(dashboardSummaryPath('registrar')),

  // Tier 2
  scheduling: createDataConfig(dashboardSummaryPath('scheduling')),
  gradebook: createDataConfig(dashboardSummaryPath('gradebook')),
  'student-care': createDataConfig(dashboardSummaryPath('student-care')),
  'activities-athletics': createDataConfig(dashboardSummaryPath('activities-athletics')),
  communications: createDataConfig(dashboardSummaryPath('communications')),

  // Tier 3
  'school-administrator': createDataConfig(dashboardSummaryPath('school-administrator')),
  'school-board': createDataConfig(dashboardSummaryPath('school-board')),
  'master-control': createDataConfig(dashboardSummaryPath('master-control')),
  admissions: createDataConfig(dashboardSummaryPath('admissions')),
  advancement: createDataConfig(dashboardSummaryPath('advancement')),

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
  'compliance-audit': createDataConfig(dashboardSummaryPath('compliance-audit'), {
    allowScaffoldFallback: true,
    fallbackData: {
      dashboard_key: 'compliance-audit',
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
        served_from: 'fallback',
        certification_candidate: 'hybrid',
        fallback_source: 'frontend_scaffold',
      },
    },
  }),
  'revenue-operations': createDataConfig(dashboardSummaryPath('revenue-operations')),
  'release-reliability': createDataConfig(dashboardSummaryPath('release-reliability'), {
    allowScaffoldFallback: true,
    fallbackData: {
      dashboard_key: 'release-reliability',
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
          secondary: 'Platform engineering follow-up required.',
        },
        {
          title: 'Two environments are not on expected build SHA',
          level: 'High',
          secondary: 'Verify deployment alignment.',
        },
        {
          title: 'Release proof packet is incomplete for one deploy',
          level: 'Medium',
          secondary: 'Complete evidence before certification.',
        },
      ],
      queue: [
        'Review failed release gate evidence',
        'Verify environment build SHA alignment',
        'Close open production incident postmortem tasks',
        'Publish release readiness summary',
      ],
      meta: {
        certification_candidate: 'hybrid',
        fallback_source: 'frontend_scaffold',
      },
    },
  }),

  // Phase 9 control page
  'dashboard-certification-center': createDataConfig(dashboardSummaryPath('dashboard-certification-center'), {
    allowScaffoldFallback: true,
    fallbackData: {
      dashboard_key: 'dashboard-certification-center',
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
        certification_candidate: 'hybrid',
        fallback_source: 'frontend_scaffold',
      },
    },
  }),
};