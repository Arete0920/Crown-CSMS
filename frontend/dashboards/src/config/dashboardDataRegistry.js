function percent(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—';
  }

  return `${Number(value).toFixed(digits)}%`;
}

function integer(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—';
  }

  return Intl.NumberFormat('en-US').format(Number(value));
}

function currency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—';
  }

  return Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function stringValue(value) {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  return String(value);
}

function normalizeAlertLevel(value) {
  const normalized = String(value || '').toLowerCase();

  if (normalized === 'critical' || normalized === 'high') return 'High';
  if (normalized === 'medium' || normalized === 'warning') return 'Medium';
  return 'Low';
}

function normalizeAlerts(items, fallbackSecondary) {
  if (!Array.isArray(items)) return [];

  return items.map((item, index) => ({
    title: item?.title || item?.label || `Alert ${index + 1}`,
    level: normalizeAlertLevel(item?.level || item?.severity),
    secondary: item?.secondary || item?.message || fallbackSecondary,
  }));
}

function normalizeQueue(items) {
  if (!Array.isArray(items)) return [];

  return items.map((item, index) => {
    if (typeof item === 'string') return item;
    return item?.title || item?.label || `Queue item ${index + 1}`;
  });
}

function identityTransform(response) {
  return response;
}

function createDataConfig(endpoint, options = {}) {
  return {
    endpoint,
    method: options.method || 'GET',
    query: options.query || undefined,
    allowScaffoldFallback: options.allowScaffoldFallback ?? true,
    fallbackData: options.fallbackData ?? null,
    transform: options.transform || identityTransform,
  };
}

function dashboardSummaryPath(slug) {
  return `/api/v1/dashboards/${slug}/summary`;
}

function transformAttendance(response) {
  return {
    metrics: [
      {
        label: 'Present Rate Today',
        value: percent(response?.metrics?.present_rate_today ?? response?.present_rate_today),
      },
      {
        label: 'Absent Students',
        value: integer(response?.metrics?.absent_students ?? response?.absent_students),
      },
      {
        label: 'Late Check-Ins',
        value: integer(response?.metrics?.late_checkins ?? response?.late_checkins),
      },
      {
        label: 'Missing Homerooms',
        value: integer(response?.metrics?.missing_homerooms ?? response?.missing_homerooms),
      },
    ],
    alerts: normalizeAlerts(
      response?.alerts,
      'Attendance follow-up required.'
    ),
    queue: normalizeQueue(response?.queue || response?.tasks),
  };
}

function transformReleaseReliability(response) {
  return {
    metrics: [
      {
        label: 'Deployments This Month',
        value: integer(response?.metrics?.deployments_this_month ?? response?.deployments_this_month),
      },
      {
        label: 'Open Production Incidents',
        value: integer(response?.metrics?.open_production_incidents ?? response?.open_production_incidents),
      },
      {
        label: 'Failed Checks in Last 24h',
        value: integer(response?.metrics?.failed_checks_24h ?? response?.failed_checks_24h),
      },
      {
        label: 'Release Readiness',
        value: stringValue(response?.metrics?.release_readiness ?? response?.release_readiness),
      },
    ],
    alerts: normalizeAlerts(
      response?.alerts,
      'Platform engineering follow-up required.'
    ),
    queue: normalizeQueue(response?.queue || response?.tasks),
  };
}

export const DASHBOARD_DATA_REGISTRY = {
  // Tier 1
  attendance: createDataConfig(dashboardSummaryPath('attendance'), {
    transform: transformAttendance,
    fallbackData: {
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
  'compliance-audit': createDataConfig(dashboardSummaryPath('compliance-audit')),
  'revenue-operations': createDataConfig(dashboardSummaryPath('revenue-operations')),
  'release-reliability': createDataConfig(dashboardSummaryPath('release-reliability'), {
    transform: transformReleaseReliability,
    fallbackData: {
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
    },
  }),

  // Phase 9 control page
  'dashboard-certification-center': createDataConfig('/api/v1/platform/dashboard-certification-center'),
};
