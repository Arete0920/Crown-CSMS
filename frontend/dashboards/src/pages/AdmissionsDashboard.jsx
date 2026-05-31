import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
import useAdmissionsDashboardData from '../hooks/useAdmissionsDashboardData.js';

function toInt(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function toPercent(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) {
    return '--';
  }
  return `${Math.round(n * 100)}%`;
}

function cloneConfig(template) {
  if (typeof globalThis.structuredClone === 'function') {
    return globalThis.structuredClone(template);
  }
  return JSON.parse(JSON.stringify(template));
}

function getDataSourceLabel(dataState) {
  if (dataState === 'live') {
    return 'Admissions summary API';
  }
  if (dataState === 'loading') {
    return 'Admissions summary API loading';
  }
  if (dataState === 'unavailable') {
    return 'Admissions summary API unavailable';
  }
  return 'Admissions template fallback';
}

export default function AdmissionsDashboard() {
  const baseConfig = getDashboardTemplate('admissions');
  const { loading, error, summary, rawSummary, timeline } = useAdmissionsDashboardData();

  const byStage = rawSummary?.pipeline?.by_stage || {};
  const hasLiveSummary = !loading && !error && Object.keys(byStage).length > 0;
  const dataState = hasLiveSummary ? 'live' : loading ? 'loading' : error ? 'unavailable' : 'fallback';
  const dataStateLabel = hasLiveSummary
    ? 'Live admissions data'
    : dataState === 'loading'
      ? 'Loading admissions data'
      : dataState === 'unavailable'
        ? 'Admissions data unavailable'
        : 'Fallback admissions data';
  const dataSourceLabel = getDataSourceLabel(dataState);

  const total = toInt(rawSummary?.pipeline?.total ?? summary?.total);
  const inquiry = toInt(byStage.inquiry);
  const submitted = toInt(byStage.application_submitted ?? summary?.submitted);
  const accepted = toInt(byStage.accepted ?? summary?.admitted);
  const enrolled = toInt(byStage.enrolled ?? summary?.enrolled);
  const declined = toInt(byStage.declined);
  const openApplications = Math.max(total - enrolled - declined, 0);
  const acceptedToEnrolled = toPercent(rawSummary?.conversion?.accepted_to_enrolled);
  const inquiryToSubmitted = toPercent(rawSummary?.conversion?.inquiry_to_submitted);
  const submittedToAccepted = toPercent(rawSummary?.conversion?.submitted_to_accepted);
  const inReview = toInt(byStage.in_review ?? summary?.underReview);
  const waitlisted = toInt(byStage.waitlisted ?? summary?.waitlisted);

  const velocity = rawSummary?.velocity_days || {};
  const velocityInquiryToTour = Number(velocity.inquiry_to_tour_completed_avg);
  const velocityTourToSubmit = Number(velocity.tour_completed_to_submitted_avg);
  const velocitySubmitToDecision = Number(velocity.submitted_to_decision_avg);
  const velocityLabel = Number.isFinite(velocitySubmitToDecision)
    ? `${Math.round(velocitySubmitToDecision)} day avg decision cycle`
    : 'Decision cycle pending more data';

  const stageAging = rawSummary?.stage_aging || {};
  const submittedAging = stageAging.application_submitted || {};
  const inReviewAging = stageAging.in_review || {};
  const acceptedAging = stageAging.accepted || {};
  const submittedOverSla = toInt(submittedAging.over_sla);
  const inReviewOverSla = toInt(inReviewAging.over_sla);
  const acceptedOverSla = toInt(acceptedAging.over_sla);
  const totalOverSla = submittedOverSla + inReviewOverSla + acceptedOverSla;
  const maxStageAgeDays = Math.max(
    toInt(submittedAging.max_days),
    toInt(inReviewAging.max_days),
    toInt(acceptedAging.max_days),
  );

  const topSource = rawSummary?.top_sources?.[0];
  const topSourceLabel = topSource?.source ? `${topSource.source} (${topSource.total})` : 'No source data yet';

  const config = cloneConfig(baseConfig);
  config.dataState = dataState;
  config.sourceLabel = dataSourceLabel;
  config.lastSyncLabel = hasLiveSummary ? 'Last synced just now' : dataStateLabel;
  config.updatesCount = hasLiveSummary ? 0 : 1;
  config.note = `${config.note} · ${dataStateLabel}`;

  config.metrics = [
    {
      label: 'Open Applications',
      value: String(openApplications),
      detail: `Total pipeline: ${total}. Excludes enrolled and declined.`,
      accent: 'blue',
      dataState,
      sourceLabel: dataSourceLabel,
    },
    {
      label: 'Inquiries',
      value: String(inquiry),
      detail: 'Prospective families at inquiry stage.',
      accent: 'navy',
      dataState,
      sourceLabel: dataSourceLabel,
    },
    {
      label: 'Accepted Students',
      value: String(accepted),
      detail: `${enrolled} already enrolled from accepted cohort.`,
      accent: 'gold',
      dataState,
      sourceLabel: dataSourceLabel,
    },
    {
      label: 'Stage Aging Pressure',
      value: `${maxStageAgeDays}d`,
      detail: `${totalOverSla} applications over SLA across submitted, review, and accepted stages.`,
      accent: totalOverSla > 0 ? 'gold' : 'emerald',
      dataState,
      sourceLabel: dataSourceLabel,
    },
  ];

  config.priorities = [
    {
      title: `${submitted} submitted applications awaiting review progression`,
      detail: 'Prioritize file review to protect decision turnaround.',
      state: submitted > 0 ? 'In Progress' : 'Ready',
      tone: submitted > 0 ? 'warn' : 'good',
    },
    {
      title: `${accepted - enrolled > 0 ? accepted - enrolled : 0} accepted families not yet enrolled`,
      detail: 'Follow up with contract and deposit completion support.',
      state: accepted - enrolled > 0 ? 'Ready' : 'Stable',
      tone: accepted - enrolled > 0 ? 'warn' : 'good',
    },
    {
      title: `${totalOverSla} admissions records over SLA`,
      detail: 'Clear stale submitted, in-review, and accepted records to protect family experience.',
      state: totalOverSla > 0 ? 'Action Required' : 'Stable',
      tone: totalOverSla > 0 ? 'warn' : 'good',
    },
  ];

  config.alerts = [
    {
      title: hasLiveSummary
        ? 'Dashboard metrics are sourced from live admissions summary API.'
        : 'Dashboard is in fallback mode until live admissions summary is available.',
      detail: hasLiveSummary
        ? 'Values reflect current tenant-scoped admissions pipeline stages.'
        : 'Verify admissions summary endpoint health and tenant/year context.',
      tone: hasLiveSummary ? 'good' : 'warn',
    },
  ];

  config.statuses = [
    { label: 'Admissions Data Source', state: dataStateLabel },
    { label: 'Summary Endpoint', state: hasLiveSummary ? 'Operational' : error ? 'Unavailable' : 'Degraded' },
    { label: 'Pipeline Coverage', state: `Inquiry ${inquiry} · Submitted ${submitted} · Accepted ${accepted} · Enrolled ${enrolled}` },
    { label: 'Stage Aging', state: totalOverSla > 0 ? `${totalOverSla} records over SLA` : 'Within SLA' },
    { label: 'Next Priority', state: submitted > 0 ? 'Review submitted applications' : 'Advance inquiry pipeline' },
  ];

  config.commandModules = [
    {
      key: 'pipeline',
      icon: 'PL',
      title: 'Application Pipeline',
      status: submitted > 0 || inReview > 0 || totalOverSla > 0 ? 'Watch' : 'Stable',
      statusTone: submitted > 0 || inReview > 0 || totalOverSla > 0 ? 'warn' : 'good',
      mainKpi: `${openApplications} open applications`,
      summary: `Submitted ${submitted} · In review ${inReview} · Waitlisted ${waitlisted}`,
      kpis: [
        { label: 'Inquiry', value: String(inquiry) },
        { label: 'Submitted', value: String(submitted) },
        { label: 'In review', value: String(inReview) },
        { label: 'Waitlisted', value: String(waitlisted) },
      ],
      details: [
        `Pipeline total: ${total}`,
        `Declined: ${declined}`,
        `Top source: ${topSourceLabel}`,
        velocityLabel,
        `Stage aging max: ${maxStageAgeDays} days`,
        `Over SLA: ${totalOverSla}`,
      ],
      dataState,
      sourceLabel: dataSourceLabel,
      primaryActionLabel: 'Review Pipeline',
      backActionLabel: 'All Applications',
      primaryActionHref: '/admissions/pipeline',
      backActionHref: '/admissions',
      lastUpdated: hasLiveSummary ? 'Live' : 'Fallback',
    },
    {
      key: 'conversion',
      icon: 'CV',
      title: 'Conversion Health',
      status: accepted > 0 ? 'Stable' : 'Watch',
      statusTone: accepted > 0 ? 'good' : 'warn',
      mainKpi: `${acceptedToEnrolled} accepted → enrolled`,
      summary: `Inquiry → submitted ${inquiryToSubmitted} · Submitted → accepted ${submittedToAccepted}`,
      kpis: [
        { label: 'Inquiry to submitted', value: inquiryToSubmitted },
        { label: 'Submitted to accepted', value: submittedToAccepted },
        { label: 'Accepted to enrolled', value: acceptedToEnrolled },
        { label: 'Accepted students', value: String(accepted) },
      ],
      details: [
        `Enrolled: ${enrolled}`,
        `Not yet enrolled from accepted: ${accepted - enrolled > 0 ? accepted - enrolled : 0}`,
        `Primary source cohort: ${topSourceLabel}`,
        velocityLabel,
      ],
      dataState,
      sourceLabel: dataSourceLabel,
      primaryActionLabel: 'Open Enrollment',
      backActionLabel: 'Pipeline View',
      primaryActionHref: '/reenrollment',
      backActionHref: '/admissions/pipeline',
      lastUpdated: hasLiveSummary ? 'Live' : 'Fallback',
    },
  ];

  config.trendPanels = [
    {
      kicker: 'Current stage distribution',
      title: 'Inquiry to enrolled funnel snapshot',
      chip: hasLiveSummary ? 'Live' : 'Fallback',
      trend: [
        { month: 'Inquiry', value: inquiry },
        { month: 'Submitted', value: submitted },
        { month: 'Accepted', value: accepted },
        { month: 'Enrolled', value: enrolled },
      ],
    },
    {
      kicker: 'Cycle velocity',
      title: 'Average days between major admissions milestones',
      chip: Number.isFinite(velocitySubmitToDecision) ? 'Measured' : 'Insufficient data',
      trend: [
        { month: 'Inquiry→Tour', value: Number.isFinite(velocityInquiryToTour) ? Math.round(velocityInquiryToTour) : 0 },
        { month: 'Tour→Submit', value: Number.isFinite(velocityTourToSubmit) ? Math.round(velocityTourToSubmit) : 0 },
        { month: 'Submit→Decision', value: Number.isFinite(velocitySubmitToDecision) ? Math.round(velocitySubmitToDecision) : 0 },
      ],
    },
  ];

  const timelineEvents = Array.isArray(timeline) ? timeline : [];
  config.activities = timelineEvents.length > 0
    ? timelineEvents
      .slice(0, 5)
      .map((event) => event.summary || event.type || event.title || 'Admissions event recorded')
    : [
      `Top source: ${topSourceLabel}`,
      `Open applications: ${openApplications}`,
      `Submitted awaiting movement: ${submitted}`,
      `Accepted awaiting enrollment: ${accepted - enrolled > 0 ? accepted - enrolled : 0}`,
      `Admissions records over SLA: ${totalOverSla}`,
      hasLiveSummary ? 'Admissions summary is live.' : 'Admissions summary is running in fallback mode.',
    ];

  return <CrownDashboardTemplate config={config} roleKey="admissions" />;
}
