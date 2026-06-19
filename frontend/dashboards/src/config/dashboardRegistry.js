import { validateDashboardRegistry } from './validateDashboardRegistry';
import { normalizeRoles as normalizeEffectiveRoles } from '../auth/roleAccess';
export { normalizeRoles } from '../auth/roleAccess';
import { PATHS } from '../routes/paths';

// Tier 1
import AttendanceDashboard from '../pages/AttendanceDashboard';
import BillingDashboard from '../pages/BillingDashboard';
import FinancialAidDashboard from '../pages/FinancialAidDashboard';
import RegistrarDashboard from '../pages/RegistrarDashboard';

// Tier 2
import SchedulingDashboard from '../pages/SchedulingDashboard';
import GradebookDashboard from '../pages/GradebookDashboard';
import StudentCareDashboard from '../pages/StudentCareDashboard';
import ActivitiesAthleticsDashboard from '../pages/ActivitiesAthleticsDashboard';
import CommunicationsDashboard from '../pages/CommunicationsDashboard';

// Tier 3
import SchoolAdministratorDashboard from '../pages/SchoolAdministratorDashboard';
import SchoolBoardDashboard from '../pages/SchoolBoardDashboard';
import MasterControlDashboard from '../pages/MasterControlDashboard';
import AdmissionsDashboard from '../pages/AdmissionsDashboard';
import AdvancementDashboard from '../pages/AdvancementDashboard';

// Tier 4
import HRDashboard from '../pages/HRDashboard';
import FacilitiesDashboard from '../pages/FacilitiesDashboard';
import HealthOfficeDashboard from '../pages/HealthOfficeDashboard';
import TransportationDashboard from '../pages/TransportationDashboard';
import FoodServiceDashboard from '../pages/FoodServiceDashboard';
import ITSupportDashboard from '../pages/ITSupportDashboard';

// Tier 5
import FineArtsDashboard from '../pages/FineArtsDashboard';
import AthleticsDirectorDashboard from '../pages/AthleticsDirectorDashboard';
import LibraryMediaDashboard from '../pages/LibraryMediaDashboard';
import ExtendedCareDashboard from '../pages/ExtendedCareDashboard';
import SummerCampDashboard from '../pages/SummerCampDashboard';
import SafetySecurityDashboard from '../pages/SafetySecurityDashboard';
import CurriculumPDDashboard from '../pages/CurriculumPDDashboard';

// Tier 6
import ChaplainSpiritualLifeDashboard from '../pages/ChaplainSpiritualLifeDashboard';
import AdvancementOperationsDashboard from '../pages/AdvancementOperationsDashboard';
import VolunteerManagementDashboard from '../pages/VolunteerManagementDashboard';
import PortraitServiceHoursDashboard from '../pages/PortraitServiceHoursDashboard';
import AlumniRelationsDashboard from '../pages/AlumniRelationsDashboard';
import NetworkBenchmarkingDashboard from '../pages/NetworkBenchmarkingDashboard';

// Tier 7
import ImplementationSuccessDashboard from '../pages/ImplementationSuccessDashboard';
import DataMigrationDashboard from '../pages/DataMigrationDashboard';
import IntegrationsAutomationDashboard from '../pages/IntegrationsAutomationDashboard';
import ComplianceAuditDashboard from '../pages/ComplianceAuditDashboard';
import RevenueOperationsDashboard from '../pages/RevenueOperationsDashboard';
import ReleaseReliabilityDashboard from '../pages/ReleaseReliabilityDashboard';
import DashboardCertificationCenter from '../pages/DashboardCertificationCenter';

const readyReadiness = () => ({
  shellReady: true,
  uxReady: true,
  accessReady: true,
  dataReady: true,
});

const placeholderReadiness = () => ({
  shellReady: true,
  uxReady: false,
  accessReady: true,
  dataReady: false,
});

const SUPER_ADMIN = ['super_admin'];
const MASTER_CONTROL = ['master_control', ...SUPER_ADMIN];
const SCHOOL_ADMIN = ['school_admin', ...MASTER_CONTROL];
const BOARD_MEMBER = ['board_member', ...MASTER_CONTROL];
const FINANCE_TEAM = ['finance_admin', ...SCHOOL_ADMIN];
const REGISTRAR_TEAM = ['registrar', ...SCHOOL_ADMIN];
const ATTENDANCE_TEAM = ['attendance_admin', ...REGISTRAR_TEAM];
const ACADEMIC_TEAM = ['academic_admin', ...SCHOOL_ADMIN];
const ADMISSIONS_TEAM = ['admissions_manager', ...SCHOOL_ADMIN];
const ADVANCEMENT_TEAM = ['advancement_officer', ...SCHOOL_ADMIN];
const HR_TEAM = ['hr_manager', ...SCHOOL_ADMIN];
const FACILITIES_TEAM = ['facilities_manager', ...SCHOOL_ADMIN];
const HEALTH_TEAM = ['nurse', 'health_office', ...SCHOOL_ADMIN];
const TRANSPORT_TEAM = ['transportation_manager', ...SCHOOL_ADMIN];
const FOOD_TEAM = ['food_service_manager', ...SCHOOL_ADMIN];
const IT_TEAM = ['it_support', ...MASTER_CONTROL];
const FINE_ARTS_TEAM = ['fine_arts_director', ...SCHOOL_ADMIN];
const ATHLETICS_TEAM = ['athletics_director', ...SCHOOL_ADMIN];
const LIBRARY_TEAM = ['librarian', 'media_specialist', ...SCHOOL_ADMIN];
const EXTENDED_CARE_TEAM = ['extended_care_manager', ...SCHOOL_ADMIN];
const SUMMER_CAMP_TEAM = ['summer_camp_coordinator', ...EXTENDED_CARE_TEAM];
const SAFETY_TEAM = ['safety_manager', 'security_officer', ...SCHOOL_ADMIN];
const CURRICULUM_TEAM = ['curriculum_director', 'pd_coordinator', ...SCHOOL_ADMIN];
const CHAPLAIN_TEAM = ['chaplain', 'spiritual_life', ...SCHOOL_ADMIN];
const VOLUNTEER_TEAM = ['volunteer_coordinator', ...SCHOOL_ADMIN];
const PORTRAIT_TEAM = ['service_learning_coordinator', ...SCHOOL_ADMIN];
const ALUMNI_TEAM = ['alumni_relations', ...ADVANCEMENT_TEAM];

const IMPLEMENTATION_TEAM = ['crown_implementation', ...MASTER_CONTROL];
const DATA_OPS_TEAM = ['crown_data_ops', ...MASTER_CONTROL];
const INTEGRATIONS_TEAM = ['crown_integrations', ...IT_TEAM];
const COMPLIANCE_TEAM = ['crown_compliance', ...MASTER_CONTROL];
const REVENUE_OPS_TEAM = ['crown_revenue_ops', ...MASTER_CONTROL];
const RELEASE_TEAM = ['crown_platform_ops', ...MASTER_CONTROL];
const PLATFORM_CERT_TEAM = [...new Set([...RELEASE_TEAM, ...COMPLIANCE_TEAM, ...MASTER_CONTROL])];

function createDashboard({
  key,
  label,
  path,
  tier,
  section,
  allowedRoles,
  roles,
  component,
  releaseState,
  fallbackPath,
  moduleKey,
  moduleType,
  owner,
  readiness,
}) {
  const effectiveReleaseState = releaseState || 'draft';
  const isReadyLike = ['ready', 'live', 'production'].includes(effectiveReleaseState);
  const effectiveReadiness = readiness || (isReadyLike ? readyReadiness() : placeholderReadiness());

  return {
    key,
    label,
    title: label,
    path,
    tier,
    section,
    allowedRoles: allowedRoles || roles || [],
    roles: roles || allowedRoles || [],
    component,
    moduleKey: moduleKey || key,
    moduleType: moduleType || 'dashboard',
    owner: owner || 'dashboardRegistry',
    releaseState: effectiveReleaseState,
    fallbackPath,
    readiness: effectiveReadiness,
  };
}

export const DASHBOARD_SECTION_ORDER = [
  'Core Operations',
  'Academic & Student Operations',
  'Leadership & Growth',
  'Specialist Operations',
  'Enrichment & Support',
  'Mission & Network',
  'Platform Operations',
];

export const DASHBOARD_REGISTRY = [
  // Tier 1
  createDashboard({
    key: 'attendance',
    label: 'Attendance',
    path: PATHS.ATTENDANCE_DASHBOARD,
    tier: 1,
    section: 'Core Operations',
    allowedRoles: ATTENDANCE_TEAM,
    component: AttendanceDashboard,
  }),
  createDashboard({
    key: 'billing',
    label: 'Billing',
    path: PATHS.BILLING_DASHBOARD,
    tier: 1,
    section: 'Core Operations',
    allowedRoles: FINANCE_TEAM,
    component: BillingDashboard,
  }),
  createDashboard({
    key: 'financial-aid',
    label: 'Financial Aid',
    path: PATHS.FINANCIAL_AID_DASHBOARD,
    tier: 1,
    section: 'Core Operations',
    allowedRoles: FINANCE_TEAM,
    component: FinancialAidDashboard,
  }),
  createDashboard({
    key: 'registrar',
    label: 'Registrar',
    path: PATHS.REGISTRAR_DASHBOARD,
    tier: 1,
    section: 'Core Operations',
    allowedRoles: REGISTRAR_TEAM,
    component: RegistrarDashboard,
  }),

  // Tier 2
  createDashboard({
    key: 'scheduling',
    label: 'Scheduling',
    path: PATHS.SCHEDULING_DASHBOARD,
    tier: 2,
    section: 'Academic & Student Operations',
    allowedRoles: REGISTRAR_TEAM,
    component: SchedulingDashboard,
  }),
  createDashboard({
    key: 'gradebook',
    label: 'Gradebook',
    path: PATHS.GRADEBOOK_DASHBOARD,
    tier: 2,
    section: 'Academic & Student Operations',
    allowedRoles: ACADEMIC_TEAM,
    component: GradebookDashboard,
  }),
  createDashboard({
    key: 'student-care',
    label: 'Student Care',
    path: PATHS.STUDENT_CARE_DASHBOARD,
    tier: 2,
    section: 'Academic & Student Operations',
    allowedRoles: ACADEMIC_TEAM,
    component: StudentCareDashboard,
  }),
  createDashboard({
    key: 'activities-athletics',
    label: 'Activities & Athletics',
    path: PATHS.ACTIVITIES_DASHBOARD,
    tier: 2,
    section: 'Academic & Student Operations',
    allowedRoles: ATHLETICS_TEAM,
    component: ActivitiesAthleticsDashboard,
  }),
  createDashboard({
    key: 'communications',
    label: 'Communications',
    path: PATHS.COMMUNICATIONS_DASHBOARD,
    tier: 2,
    section: 'Academic & Student Operations',
    allowedRoles: SCHOOL_ADMIN,
    component: CommunicationsDashboard,
  }),

  // Tier 3
  createDashboard({
    key: 'school-administrator',
    label: 'School Administrator',
    path: PATHS.SCHOOL_ADMIN_DASHBOARD,
    tier: 3,
    section: 'Leadership & Growth',
    allowedRoles: SCHOOL_ADMIN,
    component: SchoolAdministratorDashboard,
    releaseState: 'draft',
  }),
  createDashboard({
    key: 'school-board',
    label: 'School Board',
    path: PATHS.SCHOOL_BOARD_DASHBOARD,
    tier: 3,
    section: 'Leadership & Growth',
    allowedRoles: BOARD_MEMBER,
    component: SchoolBoardDashboard,
  }),
  createDashboard({
    key: 'master-control',
    label: 'Master Control',
    path: PATHS.MASTER_CONTROL_DASHBOARD,
    tier: 3,
    section: 'Leadership & Growth',
    allowedRoles: MASTER_CONTROL,
    component: MasterControlDashboard,
  }),
  createDashboard({
    key: 'admissions',
    label: 'Admissions',
    path: PATHS.ADMISSIONS_DASHBOARD,
    tier: 3,
    section: 'Leadership & Growth',
    allowedRoles: ADMISSIONS_TEAM,
    component: AdmissionsDashboard,
  }),
  createDashboard({
    key: 'advancement',
    label: 'Advancement',
    path: PATHS.ADVANCEMENT_DASHBOARD,
    tier: 3,
    section: 'Leadership & Growth',
    allowedRoles: ADVANCEMENT_TEAM,
    component: AdvancementDashboard,
  }),

  // Tier 4
  createDashboard({
    key: 'hr',
    label: 'HR',
    path: PATHS.HR_DASHBOARD,
    tier: 4,
    section: 'Specialist Operations',
    allowedRoles: HR_TEAM,
    component: HRDashboard,
  }),
  createDashboard({
    key: 'facilities',
    label: 'Facilities',
    path: PATHS.FACILITIES_DASHBOARD,
    tier: 4,
    section: 'Specialist Operations',
    allowedRoles: FACILITIES_TEAM,
    component: FacilitiesDashboard,
  }),
  createDashboard({
    key: 'health-office',
    label: 'Health Office',
    path: PATHS.HEALTH_OFFICE_DASHBOARD,
    tier: 4,
    section: 'Specialist Operations',
    allowedRoles: HEALTH_TEAM,
    component: HealthOfficeDashboard,
  }),
  createDashboard({
    key: 'transportation',
    label: 'Transportation',
    path: PATHS.TRANSPORTATION_DASHBOARD,
    tier: 4,
    section: 'Specialist Operations',
    allowedRoles: TRANSPORT_TEAM,
    component: TransportationDashboard,
  }),
  createDashboard({
    key: 'food-service',
    label: 'Food Service',
    path: PATHS.FOOD_SERVICE_DASHBOARD,
    tier: 4,
    section: 'Specialist Operations',
    allowedRoles: FOOD_TEAM,
    component: FoodServiceDashboard,
  }),
  createDashboard({
    key: 'it-support',
    label: 'IT Support',
    path: PATHS.IT_SUPPORT_DASHBOARD,
    tier: 4,
    section: 'Specialist Operations',
    allowedRoles: IT_TEAM,
    component: ITSupportDashboard,
  }),

  // Tier 5
  createDashboard({
    key: 'fine-arts',
    label: 'Fine Arts',
    path: PATHS.FINE_ARTS_DASHBOARD,
    tier: 5,
    section: 'Enrichment & Support',
    allowedRoles: FINE_ARTS_TEAM,
    component: FineArtsDashboard,
  }),
  createDashboard({
    key: 'athletics-director',
    label: 'Athletics Director',
    path: PATHS.ATHLETICS_DIRECTOR_DASHBOARD,
    tier: 5,
    section: 'Enrichment & Support',
    allowedRoles: ATHLETICS_TEAM,
    component: AthleticsDirectorDashboard,
  }),
  createDashboard({
    key: 'library-media',
    label: 'Library / Media',
    path: PATHS.LIBRARY_MEDIA_DASHBOARD,
    tier: 5,
    section: 'Enrichment & Support',
    allowedRoles: LIBRARY_TEAM,
    component: LibraryMediaDashboard,
  }),
  createDashboard({
    key: 'extended-care',
    label: 'Extended Care',
    path: PATHS.EXTENDED_CARE_DASHBOARD,
    tier: 5,
    section: 'Enrichment & Support',
    allowedRoles: EXTENDED_CARE_TEAM,
    component: ExtendedCareDashboard,
  }),
  createDashboard({
    key: 'summer-camp',
    label: 'Summer Camp',
    path: PATHS.SUMMER_CAMP_DASHBOARD,
    tier: 5,
    section: 'Enrichment & Support',
    allowedRoles: SUMMER_CAMP_TEAM,
    component: SummerCampDashboard,
  }),
  createDashboard({
    key: 'safety-security',
    label: 'Safety / Security',
    path: PATHS.SAFETY_SECURITY_DASHBOARD,
    tier: 5,
    section: 'Enrichment & Support',
    allowedRoles: SAFETY_TEAM,
    component: SafetySecurityDashboard,
  }),
  createDashboard({
    key: 'curriculum-pd',
    label: 'Curriculum / PD Hub',
    path: PATHS.CURRICULUM_PD_DASHBOARD,
    tier: 5,
    section: 'Enrichment & Support',
    allowedRoles: CURRICULUM_TEAM,
    component: CurriculumPDDashboard,
  }),

  // Tier 6
  createDashboard({
    key: 'chaplain-spiritual-life',
    label: 'Chaplain / Spiritual Life',
    path: PATHS.CHAPLAIN_DASHBOARD,
    tier: 6,
    section: 'Mission & Network',
    allowedRoles: CHAPLAIN_TEAM,
    component: ChaplainSpiritualLifeDashboard,
  }),
  createDashboard({
    key: 'advancement-operations',
    label: 'Advancement Operations',
    path: PATHS.ADVANCEMENT_OPERATIONS_DASHBOARD,
    tier: 6,
    section: 'Mission & Network',
    allowedRoles: ADVANCEMENT_TEAM,
    component: AdvancementOperationsDashboard,
  }),
  createDashboard({
    key: 'volunteer-management',
    label: 'Volunteer Management',
    path: PATHS.VOLUNTEER_MANAGEMENT_DASHBOARD,
    tier: 6,
    section: 'Mission & Network',
    allowedRoles: VOLUNTEER_TEAM,
    component: VolunteerManagementDashboard,
  }),
  createDashboard({
    key: 'portrait-service',
    label: 'Portrait / Service Hours',
    path: PATHS.PORTRAIT_SERVICE_DASHBOARD,
    tier: 6,
    section: 'Mission & Network',
    allowedRoles: PORTRAIT_TEAM,
    component: PortraitServiceHoursDashboard,
  }),
  createDashboard({
    key: 'alumni-relations',
    label: 'Alumni Relations',
    path: PATHS.ALUMNI_RELATIONS_DASHBOARD,
    tier: 6,
    section: 'Mission & Network',
    allowedRoles: ALUMNI_TEAM,
    component: AlumniRelationsDashboard,
  }),
  createDashboard({
    key: 'network-benchmarking',
    label: 'Network Benchmarking',
    path: PATHS.NETWORK_BENCHMARKING_DASHBOARD,
    tier: 6,
    section: 'Mission & Network',
    allowedRoles: MASTER_CONTROL,
    component: NetworkBenchmarkingDashboard,
  }),

  // Tier 7
  createDashboard({
    key: 'implementation-success',
    label: 'Implementation Success',
    path: PATHS.IMPLEMENTATION_SUCCESS_DASHBOARD,
    tier: 7,
    section: 'Platform Operations',
    allowedRoles: IMPLEMENTATION_TEAM,
    component: ImplementationSuccessDashboard,
  }),
  createDashboard({
    key: 'data-migration',
    label: 'Data Migration',
    path: PATHS.DATA_MIGRATION_DASHBOARD,
    tier: 7,
    section: 'Platform Operations',
    allowedRoles: DATA_OPS_TEAM,
    component: DataMigrationDashboard,
  }),
  createDashboard({
    key: 'integrations-automation',
    label: 'Integrations / Automation',
    path: PATHS.INTEGRATIONS_AUTOMATION_DASHBOARD,
    tier: 7,
    section: 'Platform Operations',
    allowedRoles: INTEGRATIONS_TEAM,
    component: IntegrationsAutomationDashboard,
  }),
  createDashboard({
    key: 'compliance-audit',
    label: 'Compliance / Audit',
    path: PATHS.COMPLIANCE_AUDIT_DASHBOARD,
    tier: 7,
    section: 'Platform Operations',
    allowedRoles: COMPLIANCE_TEAM,
    component: ComplianceAuditDashboard,
  }),
  createDashboard({
    key: 'revenue-operations',
    label: 'Revenue Operations',
    path: PATHS.REVENUE_OPERATIONS_DASHBOARD,
    tier: 7,
    section: 'Platform Operations',
    allowedRoles: REVENUE_OPS_TEAM,
    component: RevenueOperationsDashboard,
  }),
  createDashboard({
    key: 'release-reliability',
    label: 'Release Reliability',
    path: PATHS.RELEASE_RELIABILITY_DASHBOARD,
    tier: 7,
    section: 'Platform Operations',
    allowedRoles: RELEASE_TEAM,
    component: ReleaseReliabilityDashboard,
    releaseState: 'ready',
  }),
  createDashboard({
    key: 'dashboard-certification-center',
    label: 'Dashboard Certification Center',
    path: PATHS.DASHBOARD_CERTIFICATION_CENTER,
    tier: 7,
    section: 'Platform Operations',
    allowedRoles: PLATFORM_CERT_TEAM,
    component: DashboardCertificationCenter,
    releaseState: 'draft',
  }),
];

export function hasRouteAccess(userRoles, allowedRoles) {
  const normalizedUserRoles = normalizeEffectiveRoles(userRoles);
  const normalizedAllowedRoles = normalizeEffectiveRoles(allowedRoles);

  if (normalizedUserRoles.includes('super_admin')) {
    return true;
  }

  return normalizedAllowedRoles.some((role) => normalizedUserRoles.includes(role));
}

export function getAccessibleDashboards(userRoles) {
  return DASHBOARD_REGISTRY.filter((item) =>
    hasRouteAccess(userRoles, item.allowedRoles)
  );
}

export function getAccessibleDashboardSections(userRoles) {
  const accessible = getAccessibleDashboards(userRoles);

  return DASHBOARD_SECTION_ORDER.map((sectionLabel) => {
    const items = accessible.filter((item) => item.section === sectionLabel);

    return {
      sectionLabel,
      items,
    };
  }).filter((section) => section.items.length > 0);
}

export function getDefaultDashboardPath(userRoles) {
  return getAccessibleDashboards(userRoles)[0]?.path || '/';
}

const isDev = typeof import.meta !== "undefined" && import.meta.env?.DEV;

if (isDev) {
  validateDashboardRegistry(DASHBOARD_REGISTRY);
}

export default DASHBOARD_REGISTRY;
