import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
import useDashboardData from '../hooks/useDashboardData.js';
import { getSelectedSchoolId } from '../utils/authClient.js';

function cloneConfig(template) {
  if (typeof globalThis.structuredClone === 'function') {
    return globalThis.structuredClone(template);
  }
  return JSON.parse(JSON.stringify(template));
}

function percent(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${Math.round(n)}%` : '--';
}

export default function MarketingDashboard() {
  const baseConfig = getDashboardTemplate('marketing');
  const dashboard = useDashboardData('marketing');
  const payload = dashboard.data || {};
  const isLive = dashboard.source === 'live' && !dashboard.error;
  const dataState = isLive ? 'live' : dashboard.loading ? 'loading' : dashboard.error ? 'unavailable' : 'fallback';
  const sourceLabel = isLive
    ? 'Tenant-scoped admissions and marketing attribution data'
    : dashboard.loading
      ? 'Marketing data loading'
      : dashboard.error
        ? 'Marketing data unavailable'
        : 'Marketing configuration fallback';

  const capture = payload.inquiry_capture;
  const inquiries = Number(capture?.captured ?? payload.inquiries ?? 0);
  const tours = Number(payload.tours_scheduled || 0);
  const applications = Number(payload.applications || 0);
  const enrolled = Number(payload.enrolled || 0);
  const stalled = Number(payload.stalled_leads || 0);
  const conversion = isLive ? Number(payload.overall_application_to_enrollment_pct) : NaN;
  const countLabel = (value) => isLive ? String(value) : '--';
  const familySources = Array.isArray(payload.inquiry_source_attribution);
  const sources = familySources ? payload.inquiry_source_attribution : Array.isArray(payload.source_attribution) ? payload.source_attribution : [];
  const inquiryActionRequired = Number(capture?.unassigned || 0) > 0 || Number(capture?.followups_due || 0) > 0;
  const actions = Array.isArray(payload.action_queue) ? payload.action_queue : [];
  const campaigns = Array.isArray(payload.campaigns) ? payload.campaigns : [];
  const primaryCampaign = campaigns[0] || null;
  const projectedGrossCents = Number(primaryCampaign?.economics?.projected_gross_tuition_cents);
  const projectedGrossLabel = Number.isFinite(projectedGrossCents) && projectedGrossCents > 0
    ? `${Math.round(projectedGrossCents / 100).toLocaleString()} gross tuition`
    : 'economics pending';
  const marketConfigured = Boolean(payload.market_intelligence && payload.market_intelligence.status !== 'not_configured');
  const advertisingConfigured = Boolean(payload.advertising && payload.advertising.status !== 'not_configured');

  const config = cloneConfig(baseConfig);
  config.disableLiveData = true;
  config.dataState = dataState;
  config.sourceLabel = sourceLabel;
  config.lastSyncLabel = isLive ? 'Last synced just now' : sourceLabel;
  config.note = isLive
    ? 'Marketing Command is operating from current tenant-scoped admissions truth.'
    : 'Marketing Command is waiting for verified live data.';

  config.metrics = [
    { label: capture ? 'Captured Inquiries' : 'Inquiry Milestones', value: countLabel(inquiries), detail: capture ? 'Families who submitted a request for information or a visit.' : 'Applications with a recorded inquiry milestone.', accent: 'blue', dataState, sourceLabel },
    { label: 'Tours Scheduled', value: countLabel(tours), detail: 'Families with a scheduled tour event.', accent: 'gold', dataState, sourceLabel },
    { label: 'Applications', value: countLabel(applications), detail: 'Non-draft applications in the active tenant.', accent: 'navy', dataState, sourceLabel },
    { label: 'Stalled Prospects', value: countLabel(stalled), detail: 'Open records with no movement for more than seven days.', accent: !isLive || stalled > 0 ? 'gold' : 'emerald', dataState, sourceLabel },
  ];

  config.priorities = !isLive
    ? [{ title: 'Marketing data unavailable', detail: 'Follow-up priorities require current school data.', state: 'Unavailable', tone: 'warn' }]
    : actions.length > 0
    ? actions.map((item) => ({
        title: item.title,
        detail: item.detail,
        state: item.state || 'Ready',
        tone: item.priority === 'high' ? 'warn' : 'good',
      }))
    : [{
        title: 'No urgent marketing follow-up detected',
        detail: 'Continue monitoring inquiry progression and source performance.',
        state: 'Stable',
        tone: 'good',
      }];

  config.alerts = [
    {
      title: marketConfigured ? 'Market intelligence configured' : 'Market intelligence not configured',
      detail: marketConfigured
        ? 'External demographic and market-opportunity inputs are available.'
        : payload.market_intelligence?.message || 'Connect approved demographic and market datasets before presenting opportunity estimates.',
      tone: marketConfigured ? 'good' : 'warn',
    },
    {
      title: advertisingConfigured ? 'Advertising attribution configured' : 'Advertising spend attribution not configured',
      detail: advertisingConfigured
        ? 'Campaign spend and outcome attribution are available.'
        : payload.advertising?.message || 'Connect approved campaign cost data before calculating advertising ROI.',
      tone: advertisingConfigured ? 'good' : 'warn',
    },
  ];

  config.commandModules = [
    {
      key: 'inquiry-follow-up', icon: 'IF', title: 'Inquiry Follow-up',
      status: !isLive || !capture ? 'Unavailable' : inquiryActionRequired ? 'Action Required' : 'Ready',
      statusTone: !isLive || !capture || inquiryActionRequired ? 'warn' : 'good',
      mainKpi: capture && isLive ? `${capture.active} active family inquiries` : 'Capture data unavailable',
      summary: 'Assign a counselor, record contact, and set the next follow-up before a family applies.',
      kpis: [
        { label: 'Captured families', value: capture ? countLabel(capture.captured) : '--' },
        { label: 'Unassigned', value: capture ? countLabel(capture.unassigned) : '--' },
        { label: 'Follow-ups due', value: capture ? countLabel(capture.followups_due) : '--' },
      ],
      details: ['Each captured inquiry remains connected to later child applications.', 'Admissions permissions govern access to family contact details.'],
      dataState: capture ? dataState : 'unavailable', sourceLabel,
      primaryActionLabel: 'Open Inquiry Queue', primaryActionHref: '/admissions/inquiries',
      backActionLabel: 'Public Inquiry Form', backActionHref: `/admissions/inquire${getSelectedSchoolId() ? `?school_id=${encodeURIComponent(getSelectedSchoolId())}` : ''}`,
      lastUpdated: capture && isLive ? 'Live' : 'Unavailable',
    },
    {
      key: 'funnel',
      icon: 'FN',
      title: 'Enrollment Funnel',
      status: !isLive ? 'Unavailable' : stalled > 0 ? 'Watch' : 'Stable',
      statusTone: !isLive || stalled > 0 ? 'warn' : 'good',
      mainKpi: `${countLabel(applications)} applications · ${countLabel(enrolled)} confirmed`,
      summary: `Application-to-enrollment conversion: ${percent(conversion)}`,
      kpis: [
        { label: 'Captured families', value: capture ? countLabel(inquiries) : '--' },
        { label: 'Tours', value: countLabel(tours) },
        { label: 'Applications', value: countLabel(applications) },
        { label: 'Confirmed applications', value: countLabel(enrolled) },
      ],
      details: [
        'Family inquiries and child applications use separate counts.',
        `Stalled prospects: ${countLabel(stalled)}`,
        `Application-to-enrollment: ${percent(conversion)}`,
        'Admissions remains the canonical enrollment workflow.',
      ],
      dataState,
      sourceLabel,
      primaryActionLabel: 'Open Admissions',
      backActionLabel: 'View Pipeline',
      primaryActionHref: '/admissions',
      backActionHref: '/admissions/pipeline',
      lastUpdated: isLive ? 'Live' : 'Unavailable',
    },
    {
      key: 'sources',
      icon: 'SR',
      title: 'Source Attribution',
      status: sources.length > 0 ? 'Stable' : 'Watch',
      statusTone: sources.length > 0 ? 'good' : 'warn',
      mainKpi: sources.length > 0 ? `${sources.length} ${familySources ? 'family inquiry' : 'legacy application'} source(s)` : 'No source attribution yet',
      summary: familySources
        ? 'Captured family inquiries by first source. Both conversion rates use inquiring families; enrollment requires at least one confirmed child application.'
        : 'Legacy application attribution: child applications and confirmed applications by intake source.',
      kpis: sources.slice(0, 4).map((row) => ({
        label: `${row.source} · ${familySources ? 'family inquiries' : 'child applications'}`,
        value: countLabel(familySources ? row.inquiries : row.applications),
      })),
      details: sources.slice(0, 5).map(
        (row) => familySources
          ? `${row.source} · Family inquiries: ${row.inquiries} · Families applied: ${row.families_applied} (${percent(row.inquiry_to_application_pct)}) · Families enrolled: ${row.families_enrolled} (${percent(row.inquiry_to_enrollment_pct)})`
          : `${row.source}: ${row.applications} child applications · ${row.enrolled} confirmed applications · ${percent(row.conversion_pct)} application-to-enrollment`
      ),
      dataState,
      sourceLabel,
      primaryActionLabel: 'Review Admissions Sources',
      backActionLabel: 'Marketing Command',
      primaryActionHref: familySources ? '/admissions/inquiries' : '/admissions/pipeline',
      backActionHref: '/marketing',
      lastUpdated: isLive ? 'Live' : 'Unavailable',
    },
    {
      key: 'capacity-growth',
      icon: 'CG',
      title: 'Capacity Growth Campaigns',
      status: primaryCampaign ? (primaryCampaign.status === 'active' ? 'Active' : 'Stable') : 'Not Configured',
      statusTone: primaryCampaign ? 'good' : 'warn',
      mainKpi: primaryCampaign
        ? `${primaryCampaign.capacity?.empty_seats ?? '--'} open seat(s) · ${primaryCampaign.funnel?.enrolled ?? 0} confirmed application(s)`
        : 'No capacity campaign configured',
      summary: primaryCampaign
        ? `${primaryCampaign.name} · Grade ${primaryCampaign.capacity?.grade_code || '--'} · ${projectedGrossLabel}`
        : 'Create a campaign that connects open seats, Portrait outcomes, affordability strategy, and enrollment conversion.',
      kpis: primaryCampaign ? [
        { label: 'Empty seats', value: String(primaryCampaign.capacity?.empty_seats ?? '--') },
        { label: 'Campaign leads', value: String(primaryCampaign.funnel?.total_leads ?? 0) },
        { label: 'Confirmed applications', value: String(primaryCampaign.funnel?.enrolled ?? 0) },
        { label: 'Follow-ups due', value: String(primaryCampaign.funnel?.followups_due ?? 0) },
      ] : [
        { label: 'Campaigns', value: '0' },
        { label: 'Empty seats', value: '--' },
        { label: 'Enrollments', value: '--' },
        { label: 'Follow-ups', value: '--' },
      ],
      details: primaryCampaign ? [
        `Unconfirmed enrollment leads: ${primaryCampaign.funnel?.unverified_enrollment_leads ?? 0}`,
        'Enrollment totals require admissions confirmation; tuition projections use configured campaign estimates.',
        `Portrait outcomes: ${(primaryCampaign.portrait || []).map((item) => item.name).join(', ') || 'Not selected'}`,
        `Projected first-year net: ${Math.round((primaryCampaign.economics?.projected_net_first_year_cents || 0) / 100).toLocaleString()}`,
        `Projected lifetime net: ${Math.round((primaryCampaign.economics?.projected_lifetime_net_tuition_cents || 0) / 100).toLocaleString()}`,
        primaryCampaign.aid?.campaign_attribution_verified
          ? 'Financial-aid campaign attribution verified.'
          : 'Financial-aid campaign attribution remains unverified until awards are explicitly linked.',
      ] : [
        'Designed to connect grade capacity, Portrait of the Graduate, Jireh affordability, campaign targeting, and enrollment economics.',
      ],
      dataState: primaryCampaign ? dataState : 'unavailable',
      sourceLabel: primaryCampaign ? sourceLabel : 'No capacity-growth campaign configured',
      primaryActionLabel: 'Marketing Command',
      backActionLabel: 'Admissions',
      primaryActionHref: '/marketing',
      backActionHref: '/admissions',
      lastUpdated: primaryCampaign ? 'Live' : 'Pending configuration',
    },
    {
      key: 'market',
      icon: 'MI',
      title: 'Market Intelligence',
      status: marketConfigured ? 'Stable' : 'Not Configured',
      statusTone: marketConfigured ? 'good' : 'warn',
      mainKpi: marketConfigured ? 'Market data connected' : 'External market data required',
      summary: payload.market_intelligence?.message || 'Demographics, drive-time, church, preschool, and competitor data are not connected.',
      kpis: [
        { label: 'Demographics', value: marketConfigured ? 'Ready' : '--' },
        { label: 'Drive-time', value: marketConfigured ? 'Ready' : '--' },
        { label: 'Church/feeder', value: marketConfigured ? 'Ready' : '--' },
        { label: 'Competitors', value: marketConfigured ? 'Ready' : '--' },
      ],
      details: [
        'Designed for addressable-family, market-penetration, feeder, and geographic opportunity analysis.',
        'No estimates are shown until verified external data are connected.',
      ],
      dataState: marketConfigured ? dataState : 'unavailable',
      sourceLabel: marketConfigured ? sourceLabel : 'External market datasets not configured',
      primaryActionLabel: 'Marketing Command',
      backActionLabel: 'Admissions',
      primaryActionHref: '/marketing',
      backActionHref: '/admissions',
      lastUpdated: marketConfigured ? 'Configured' : 'Pending integration',
    },
    {
      key: 'advertising',
      icon: 'AD',
      title: 'Advertising ROI',
      status: advertisingConfigured ? 'Stable' : 'Not Configured',
      statusTone: advertisingConfigured ? 'good' : 'warn',
      mainKpi: advertisingConfigured ? 'Campaign attribution connected' : 'Spend data required',
      summary: payload.advertising?.message || 'Advertising ROI requires verified spend and campaign-attribution data.',
      kpis: [
        { label: 'Spend', value: '--' },
        { label: 'Cost / inquiry', value: '--' },
        { label: 'Cost / application', value: '--' },
        { label: 'Cost / enrollment', value: '--' },
      ],
      details: [
        'Will connect campaign spend to inquiry, application, and enrollment outcomes.',
        'Crown will not calculate ROI from unverified or manually assumed spend.',
      ],
      dataState: advertisingConfigured ? dataState : 'unavailable',
      sourceLabel: advertisingConfigured ? sourceLabel : 'Advertising data not configured',
      primaryActionLabel: 'Marketing Command',
      backActionLabel: 'Reports',
      primaryActionHref: '/marketing',
      backActionHref: '/reports',
      lastUpdated: advertisingConfigured ? 'Configured' : 'Pending integration',
    },
  ];

  config.trendPanels = [];
  config.quickActions = [
    { title: 'Inquiry follow-up', eyebrow: 'Admissions', description: 'Assign and follow up with prospective families.', actionLabel: 'Open Inquiry Queue', href: '/admissions/inquiries' },
    { title: 'Applications', eyebrow: 'Admissions', description: 'Review the submitted application pipeline.', actionLabel: 'Open Applications', href: '/admissions/pipeline' },
  ];
  config.activities = [
    `Tracked sources: ${sources.length}`,
    `Open stalled prospect records: ${stalled}`,
    marketConfigured ? 'Market intelligence data connected.' : 'Market intelligence integration pending.',
    advertisingConfigured ? 'Advertising attribution connected.' : 'Advertising attribution integration pending.',
  ];
  config.statuses = [
    { label: 'Marketing Data Source', state: sourceLabel },
    { label: 'Admissions Attribution', state: sources.length > 0 ? 'Active' : 'Needs source data' },
    { label: 'Market Intelligence', state: marketConfigured ? 'Configured' : 'Not configured' },
    { label: 'Advertising Attribution', state: advertisingConfigured ? 'Configured' : 'Not configured' },
  ];

  return <CrownDashboardTemplate config={config} roleKey="marketing" />;
}
