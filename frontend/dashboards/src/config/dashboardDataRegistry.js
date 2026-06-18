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
        { label: 'Active Audits', value: '3' },
        { label: 'Controls Passing', value: '86%' },
        { label: 'Open Findings', value: '4' },
        { label: 'Reviews Due (30d)', value: '6' },
      ],
      alerts: [
        {
          title: 'Diocese evidence package is due soon',
          level: 'High',
          secondary: 'Complete the final evidence submission before the audit window opens.',
        },
        {
          title: 'Four open findings need remediation plans',
          level: 'High',
          secondary: 'Assign owners and document next actions this week.',
        },
      ],
      queue: [
        'Submit the Diocese audit evidence package',
        'Remediate open findings with owners and dates',
        'Schedule upcoming compliance reviews',
        'Close the current evidence collection cycle',
      ],
      meta: {
        served_from: 'sample',
        certification_candidate: 'hybrid',
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
        served_from: 'sample',
        certification_candidate: 'hybrid',
      },
    },
  }),

  // Phase 9 control page
  'dashboard-certification-center': createDataConfig(dashboardSummaryPath('dashboard-certification-center'), {
    allowScaffoldFallback: true,
    fallbackData: {
      dashboard_key: 'dashboard-certification-center',
      metrics: [
        { label: 'Dashboards Certified', value: '41' },
        { label: 'Pending Review', value: '6' },
        { label: 'Failed Certification', value: '2' },
        { label: 'Cert Rate', value: '91%' },
      ],
      alerts: [
        {
          title: 'Six dashboards are still in the review queue',
          level: 'High',
          secondary: 'Clear the queue before end of week.',
        },
        {
          title: 'Two failed dashboards need correction guidance',
          level: 'Medium',
          secondary: 'Return feedback packages before resubmission.',
        },
      ],
      queue: [
        'Complete review queue clearance',
        'Return correction guidance for failed dashboards',
        'Publish the quarterly certification report',
        'Verify reviewer training records',
      ],
      meta: {
        served_from: 'sample',
        certification_candidate: 'hybrid',
      },
    },
  }),
};
