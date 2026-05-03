import schoolAdministratorDashboard from './schoolAdministratorDashboard.js';
import teacherDashboard from './teacherDashboard.js';
import parentDashboard from './parentDashboard.js';
import studentDashboard from './studentDashboard.js';
import admissionsDashboard from './admissionsDashboard.js';
import attendanceDashboard from './attendanceDashboard.js';
import gradebookDashboard from './gradebookDashboard.js';
import financeDashboard from './financeDashboard.js';
import communicationsDashboard from './communicationsDashboard.js';
import boardDashboard from './boardDashboard.js';
import itDashboard from './itDashboard.js';
import marketingDashboard from './marketingDashboard.js';
import spiritualLifeDashboard from './spiritualLifeDashboard.js';
import officeDashboard from './officeDashboard.js';
import healthDashboard from './healthDashboard.js';
import counselingDashboard from './counselingDashboard.js';
import foodDashboard from './foodDashboard.js';
import athleticsDashboard from './athleticsDashboard.js';
import registrarDashboard from './registrarDashboard.js';
import billingDashboard from './billingDashboard.js';
import financialAidDashboard from './financialAidDashboard.js';
import schedulingDashboard from './schedulingDashboard.js';
import studentCareDashboard from './studentCareDashboard.js';
import activitiesAthleticsDashboard from './activitiesAthleticsDashboard.js';
import masterControlDashboard from './masterControlDashboard.js';
import advancementDashboard from './advancementDashboard.js';
import hrDashboard from './hrDashboard.js';
import facilitiesDashboard from './facilitiesDashboard.js';
import transportationDashboard from './transportationDashboard.js';
import fineArtsDashboard from './fineArtsDashboard.js';
import libraryMediaDashboard from './libraryMediaDashboard.js';
import extendedCareDashboard from './extendedCareDashboard.js';
import safetySecurityDashboard from './safetySecurityDashboard.js';
import curriculumPDDashboard from './curriculumPDDashboard.js';
import volunteerManagementDashboard from './volunteerManagementDashboard.js';
import portraitServiceDashboard from './portraitServiceDashboard.js';
import alumniRelationsDashboard from './alumniRelationsDashboard.js';
import networkBenchmarkingDashboard from './networkBenchmarkingDashboard.js';
import implementationSuccessDashboard from './implementationSuccessDashboard.js';
import dataMigrationDashboard from './dataMigrationDashboard.js';
import integrationsAutomationDashboard from './integrationsAutomationDashboard.js';
import complianceAuditDashboard from './complianceAuditDashboard.js';
import revenueOperationsDashboard from './revenueOperationsDashboard.js';
import advancementOperationsDashboard from './advancementOperationsDashboard.js';
import releaseReliabilityDashboard from './releaseReliabilityDashboard.js';
import dashboardCertificationCenterDashboard from './dashboardCertificationCenterDashboard.js';

export const DASHBOARD_TEMPLATE_MAP = {
  dashboard: schoolAdministratorDashboard,
  schoolAdministrator: schoolAdministratorDashboard,
  teacher: teacherDashboard,
  parent: parentDashboard,
  student: studentDashboard,
  admissions: admissionsDashboard,
  attendance: attendanceDashboard,
  gradebook: gradebookDashboard,
  finance: financeDashboard,
  communications: communicationsDashboard,
  board: boardDashboard,
  it: itDashboard,
  marketing: marketingDashboard,
  spiritualLife: spiritualLifeDashboard,
  office: officeDashboard,
  health: healthDashboard,
  counseling: counselingDashboard,
  food: foodDashboard,
  athletics: athleticsDashboard,
  registrar: registrarDashboard,
  billing: billingDashboard,
  financialAid: financialAidDashboard,
  scheduling: schedulingDashboard,
  studentCare: studentCareDashboard,
  activitiesAthletics: activitiesAthleticsDashboard,
  masterControl: masterControlDashboard,
  advancement: advancementDashboard,
  hr: hrDashboard,
  facilities: facilitiesDashboard,
  transportation: transportationDashboard,
  fineArts: fineArtsDashboard,
  libraryMedia: libraryMediaDashboard,
  extendedCare: extendedCareDashboard,
  safetySecurity: safetySecurityDashboard,
  curriculumPD: curriculumPDDashboard,
  volunteerManagement: volunteerManagementDashboard,
  portraitService: portraitServiceDashboard,
  alumniRelations: alumniRelationsDashboard,
  networkBenchmarking: networkBenchmarkingDashboard,
  implementationSuccess: implementationSuccessDashboard,
  dataMigration: dataMigrationDashboard,
  integrationsAutomation: integrationsAutomationDashboard,
  complianceAudit: complianceAuditDashboard,
  revenueOperations: revenueOperationsDashboard,
  advancementOperations: advancementOperationsDashboard,
  releaseReliability: releaseReliabilityDashboard,
  dashboardCertificationCenter: dashboardCertificationCenterDashboard,
  // Alias keys
  schoolBoard: boardDashboard,
  healthOffice: healthDashboard,
  foodService: foodDashboard,
  itSupport: itDashboard,
  athleticsDirector: athleticsDashboard,
  chaplainSpiritualLife: spiritualLifeDashboard,
};

function isValidDashboardTemplate(template) {
  return Boolean(
    template
    && typeof template === 'object'
    && typeof template.title === 'string'
    && Array.isArray(template.metrics)
  );
}

export function getDashboardTemplate(key) {
  const candidate = DASHBOARD_TEMPLATE_MAP[key] || schoolAdministratorDashboard;
  return isValidDashboardTemplate(candidate) ? candidate : schoolAdministratorDashboard;
}
