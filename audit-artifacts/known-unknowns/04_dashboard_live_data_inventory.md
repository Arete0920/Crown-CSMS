=== DASHBOARD LIVE-DATA INVENTORY ===
## Static/preview/sandbox indicators
frontend/dashboards/src/config\moduleReadiness.test.js:29:  it("prevents placeholder signals on routes marked ready", () => {
frontend/dashboards/src/components/crown-dashboard\CrownHeroHeader.jsx:25:            placeholder="Search students, workflows, and actions"
frontend/dashboards/src/config\shellOwnership.test.js:53:  it("does not expose likely placeholder links as active nav entries", () => {
frontend/dashboards/src/config\moduleReadiness.js:142:  const placeholderComponentPattern =
frontend/dashboards/src/config\moduleReadiness.js:143:    /(placeholder|comingsoon|coming_soon|notready|underconstruction|unavailable)/i;
frontend/dashboards/src/config\moduleReadiness.js:150:        placeholderComponentPattern.test(componentName)
frontend/dashboards/src/config\moduleReadiness.js:154:      type: "placeholder-signal-on-ready-route",
frontend/dashboards/src/config\moduleReadiness.js:208:    placeholderSignalCount: getReadyRoutesWithPlaceholderSignals().length,
frontend/dashboards/src/config\shellCertification.js:40:  const staticEntries = STATIC_SHELL_PATHS.map((path) => ({
frontend/dashboards/src/config\shellCertification.js:43:    owner: "staticShell",
frontend/dashboards/src/config\shellCertification.js:47:    ...annotate(staticEntries, "staticShell"),
frontend/dashboards/src/config\releaseState.js:6:  PLACEHOLDER: "placeholder",
frontend/dashboards/src/config\releaseState.js:27:  /(coming soon|placeholder|under construction|not ready|unavailable|future module|future release)/i;
frontend/dashboards/src/config\shellOwnership.js:162:  const placeholderPattern =
frontend/dashboards/src/config\shellOwnership.js:163:    /(coming-soon|placeholder|under-construction|not-ready|unavailable)/i;
frontend/dashboards/src/config\shellOwnership.js:175:    return placeholderPattern.test(text);
frontend/dashboards/src/config\dashboardRegistry.js:65:const placeholderReadiness = () => ({
frontend/dashboards/src/config\dashboardRegistry.js:124:  const effectiveReadiness = readiness || (effectiveReleaseState === 'ready' ? readyReadiness() : placeholderReadiness());
frontend/dashboards/src/config\shellCertification.test.js:22:  it("prevents placeholder-like routes from being marked ready", () => {
frontend/dashboards/src/config\dashboardTemplates\athleticsDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\athleticsDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\advancementDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\advancementDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\activitiesAthleticsDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\activitiesAthleticsDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\alumniRelationsDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\alumniRelationsDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\advancementOperationsDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\advancementOperationsDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\attendanceDashboard.js:1:import { BASE_NOTE, BASE_STATUS, BASE_TREND } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\attendanceDashboard.js:10:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\admissionsDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\admissionsDashboard.js:36:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\billingDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\billingDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\communicationsDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\communicationsDashboard.js:36:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\boardDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\boardDashboard.js:34:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\counselingDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\counselingDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\complianceAuditDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\complianceAuditDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\curriculumPDDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\curriculumPDDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\dashboardCertificationCenterDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\dashboardCertificationCenterDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\dataMigrationDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\dataMigrationDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\extendedCareDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\extendedCareDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\financeDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\financeDashboard.js:36:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\facilitiesDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\facilitiesDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\financialAidDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\financialAidDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\fineArtsDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\fineArtsDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\foodDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\foodDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\gradebookDashboard.js:1:import { BASE_NOTE, BASE_STATUS, BASE_TREND } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\gradebookDashboard.js:10:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\healthDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\healthDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\hrDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\hrDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\implementationSuccessDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\implementationSuccessDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\integrationsAutomationDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\integrationsAutomationDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\libraryMediaDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\libraryMediaDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\masterControlDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\masterControlDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\itDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\itDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\marketingDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\marketingDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\registrarDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\registrarDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\portraitServiceDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\portraitServiceDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\parentDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\parentDashboard.js:37:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\officeDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\officeDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\networkBenchmarkingDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\networkBenchmarkingDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\releaseReliabilityDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\releaseReliabilityDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\revenueOperationsDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\revenueOperationsDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\safetySecurityDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\safetySecurityDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\schedulingDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\schedulingDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\spiritualLifeDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\spiritualLifeDashboard.js:21:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\studentCareDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\studentCareDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\_baseData.js:11:export const BASE_NOTE = 'Sandbox preview data shown. Connect backend for live records.';
frontend/dashboards/src/config\dashboardTemplates\teacherDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\teacherDashboard.js:37:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\volunteerManagementDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\volunteerManagementDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\transportationDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\transportationDashboard.js:23:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\studentDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\studentDashboard.js:37:  note: BASE_NOTE,
frontend/dashboards/src/config\dashboardTemplates\schoolAdministratorDashboard.js:1:import { BASE_NOTE } from './_baseData.js';
frontend/dashboards/src/config\dashboardTemplates\schoolAdministratorDashboard.js:34:  note: BASE_NOTE,
## Dashboard template sources
frontend/dashboards/src/components/crown-dashboard\CrownDashboardTemplate.jsx:16:import { BASE_FAITH_COMMUNITY } from '../../config/dashboardTemplates/_baseData.js';
frontend/dashboards/src/components/crown-dashboard\CrownDashboardTemplate.jsx:33:  const metrics = Array.isArray(config.metrics) ? config.metrics : [];
frontend/dashboards/src/components/crown-dashboard\CrownDashboardTemplate.jsx:34:  const statuses = Array.isArray(config.statuses) ? config.statuses : [];
frontend/dashboards/src/components/crown-dashboard\CrownDashboardTemplate.jsx:35:  const activities = Array.isArray(config.activities) ? config.activities : [];
frontend/dashboards/src/components/crown-dashboard\CrownDashboardTemplate.jsx:68:      <CrownFaithCommunityStrip faithCommunity={config.faithCommunity ?? BASE_FAITH_COMMUNITY} />
frontend/dashboards/src/config\dashboardTemplates\_baseData.js:34:export const BASE_FAITH_COMMUNITY = {
