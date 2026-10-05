import { createBrowserRouter, Navigate } from "react-router";

// No-op touch to ensure required route/dashboard gate contexts run on this PR.

import RoleDashboardPage from "../pages/RoleDashboardPage.jsx";
import BillingDashboard from "../pages/BillingDashboard.jsx";
import FinancialAidDashboard from "../pages/FinancialAidDashboard.jsx";
import { AcademicsDashboard } from "../pages/AcademicsDashboard.jsx";
import { GradebookRO } from "../pages/GradebookRO.jsx";
import { TranscriptRO } from "../pages/TranscriptRO.jsx";
import { CategoryWeightsEditor } from "../pages/CategoryWeightsEditor.jsx";
import { AdmissionsPipelineList } from "../pages/AdmissionsPipelineList.jsx";
import FinanceInvoicesList from "../pages/FinanceInvoicesList.jsx";
import ParentApplicationFeePaymentPage from "../pages/ParentApplicationFeePaymentPage.jsx";
import CommunicationsThreadsList from "../pages/CommunicationsThreadsList.jsx";
import ClassroomsDashboard from "../pages/ClassroomsDashboard.jsx";
import ServiceHoursPage from "../pages/ServiceHoursPage.jsx";
import Student360Page from "../pages/Student360Page.jsx";
import ParentStudent360Page from "../pages/ParentStudent360Page.jsx";
import CrownPassMyTicketsPage from "../pages/CrownPassMyTicketsPage.jsx";
import CrownPassScannerPage from "../pages/CrownPassScannerPage.jsx";
import AcademicsTeacherGrading from "../pages/AcademicsTeacherGrading.jsx";
import AcademicsStudentWork from "../pages/AcademicsStudentWork.jsx";
import AcademicsParentSnapshot from "../pages/AcademicsParentSnapshot.jsx";
import TeacherDashboard from "../pages/TeacherDashboard.jsx";
import ParentDashboard from "../pages/ParentDashboard.jsx";
import ParentFinancialAidPreparationPage from "../pages/ParentFinancialAidPreparationPage.jsx";
import ParentLifecycleStatusCenterPage from "../pages/ParentLifecycleStatusCenterPage.jsx";
import StudentDashboard from "../pages/StudentDashboard.jsx";
import RoleHomeRedirect from "../pages/RoleHomeRedirect.jsx";
import TeacherAttendancePage from "../pages/TeacherAttendancePage.jsx";
import ParentAttendancePage from "../pages/ParentAttendancePage.jsx";
import AdmissionsStartPage from "../pages/AdmissionsStartPage.jsx";
import ProspectiveFamilyAdmissionsWizard from "../pages/ProspectiveFamilyAdmissionsWizard.jsx";
import AdmissionsChecklistHubPage from "../pages/AdmissionsChecklistHubPage.jsx";
import LoginPage from "../pages/LoginPage.jsx";
import LogoutPage from "../pages/LogoutPage.jsx";
import SandboxLandingPage from "../pages/SandboxLandingPage.jsx";
import IntegrityDashboard from "../pages/IntegrityDashboard.jsx";
import AdminDashboard from "../pages/AdminDashboard.jsx";
import SchoolAdministratorDashboard from "../pages/SchoolAdministratorDashboard.jsx";
import BoardDashboard from "../pages/BoardDashboard.jsx";
import FinanceDashboard from "../pages/FinanceDashboard.jsx";
import ITDashboard from "../pages/ITDashboard.jsx";
import MarketingDashboard from "../pages/MarketingDashboard.jsx";
import SpiritualLifeDashboard from "../pages/SpiritualLifeDashboard.jsx";
import OfficeDashboard from "../pages/OfficeDashboard.jsx";
import HealthDashboard from "../pages/HealthDashboard.jsx";
import CounselingDashboard from "../pages/CounselingDashboard.jsx";
import FoodDashboard from "../pages/FoodDashboard.jsx";
import AthleticsDashboard from "../pages/AthleticsDashboard.jsx";
import SchedulingDashboard from "../pages/SchedulingDashboard.jsx";
import CurriculumPDDashboard from "../pages/CurriculumPDDashboard.jsx";
import AdvancementDashboard from "../pages/AdvancementDashboard.jsx";
import TransportationDashboard from "../pages/TransportationDashboard.jsx";
import FacilitiesDashboard from "../pages/FacilitiesDashboard.jsx";
import SecurityDashboard from "../pages/SecurityDashboard.jsx";
import AcademicSupportDashboard from "../pages/AcademicSupportDashboard.jsx";
import FineArtsDashboard from "../pages/FineArtsDashboard.jsx";
import LibraryDashboard from "../pages/LibraryDashboard.jsx";
import ExtendedCareDashboard from "../pages/ExtendedCareDashboard.jsx";
import SummerCampRosterPage from "../pages/SummerCampRosterPage.jsx";
import RegistrarDashboard from "../pages/RegistrarDashboard.jsx";
import CommunicationsDirectorDashboard from "../pages/CommunicationsDirectorDashboard.jsx";
import PDDashboard from "../pages/PDDashboard.jsx";
import StudentServicesDashboard from "../pages/StudentServicesDashboard.jsx";
import HumanResources from "../pages/HumanResources.jsx";
import SafetyDashboard from "../pages/SafetyDashboard.jsx";
import BoardExecutiveDashboard from "../pages/BoardExecutiveDashboard.jsx";
import AftercareRosterPage from "../pages/AftercareRosterPage.jsx";
import AftercareSetupWizard from "../pages/wizards/AftercareSetupWizard.jsx";
import SummerCampSetupWizard from "../pages/wizards/SummerCampSetupWizard.jsx";
import FinanceSetupWizard from "../pages/wizards/FinanceSetupWizard.jsx";
import NotAuthorized from "../pages/NotAuthorized.jsx";
import RoleRouteGuard from "../components/routing/RoleRouteGuard.jsx";
import ParentJourneyRouteGuard from "../components/routing/ParentJourneyRouteGuard.jsx";
import RoleGuard from "./RoleGuard.jsx";
import RequirePermission from "../components/auth/RequirePermission.jsx";
import { APP_PERMISSIONS } from "../auth/permissions";
import ForbiddenPage from "../pages/ForbiddenPage.jsx";
import SystemStatusPage from "../pages/SystemStatusPage.jsx";
import ReleaseReadinessPage from "../pages/ReleaseReadinessPage.jsx";
import DemoReadinessPage from "../pages/DemoReadinessPage.jsx";
import NotFoundPage from "../pages/NotFoundPage.jsx";
import CrownLaunchDashboardPage from "../pages/CrownLaunchDashboardPage.jsx";
import CrownLaunchModulePage from "../pages/CrownLaunchModulePage.jsx";
import SchoolSettingsPage from "../pages/SchoolSettingsPage.jsx";
import MyElectronicFormsPage from "../pages/MyElectronicFormsPage.jsx";
import SandboxCommandCenter from "../pages/SandboxCommandCenter.jsx";
import { dashboardRoutes } from "./dashboardRoutes";
import { wizardRoutes } from "./wizards.js";
import { PATHS } from "./paths";
import { ROLE_GROUPS } from "./routeGroups";
import WizardHub from "../pages/WizardHub.jsx";
import FamilyAccountDetail from "../pages/FamilyAccountDetail.jsx";
import SavedPaymentMethodsPage from "../pages/SavedPaymentMethodsPage.jsx";
import FamilyStatementExportPage from "../pages/FamilyStatementExportPage.jsx";
import PaymentExceptionsQueue from "../pages/PaymentExceptionsQueue.jsx";
import {
  CurriculumImportPage,
  DualEnrollmentTrackerPage,
  InterventionCoursesPage,
  MicrosoftEducationHealthPage,
  OnlineLearningCommandCenter,
  ParentLearningStatusPage,
  StudentTodayPage,
  TeacherDailyCockpitPage,
} from "../pages/LearningContinuityWorkflows.jsx";

const FINANCE_ALLOWED_ROLES = [
  "super_admin",
  "school_admin",
  "head_of_school",
  "finance_admin",
  "finance",
  "biz_office",
  "finance_director",
  "admin",
  "director",
  "principal",
];

const FINANCIAL_AID_ALLOWED_ROLES = [
  ...FINANCE_ALLOWED_ROLES,
  "aid_director",
  "financial_aid",
];

const LEARNING_COMMAND_ALLOWED_ROLES = [
  "super_admin",
  "school_admin",
  "head_of_school",
  "principal",
  "academic_admin",
  "registrar",
  "admin",
];

const STUDENT_LEARNING_ALLOWED_ROLES = [
  "super_admin",
  "school_admin",
  "head_of_school",
  "academic_admin",
  "teacher",
  "registrar",
  "parent",
  "student",
];

const MICROSOFT_EDUCATION_ALLOWED_ROLES = [
  "super_admin",
  "school_admin",
  "head_of_school",
  "academic_admin",
  "it_admin",
  "admin",
];

const CROWNPASS_SCANNER_ROLES = [
  "super_admin",
  "school_admin",
  "head_of_school",
  "athletics_director",
  "activities_director",
  "advancement",
  "admin",
];

const IS_SANDBOX = Boolean(import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1");
const IS_LAUNCH_PREVIEW = Boolean(import.meta.env.DEV || IS_SANDBOX || import.meta.env.VITE_LAUNCH_UI_TAKEOVER === '1');

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RoleHomeRedirect />,
  },
  {
    path: PATHS.SANDBOX,
    element: <SandboxLandingPage />,
  },
  {
    path: PATHS.SANDBOX_COMMAND_CENTER,
    element: <SandboxCommandCenter />,
  },
  {
    path: PATHS.DASHBOARD,
    element: (IS_LAUNCH_PREVIEW
      ? <CrownLaunchDashboardPage activePath="/dashboard" />
      : <RoleHomeRedirect />),
  },
  {
    path: '/director/aid/*',
    element: (IS_SANDBOX
      ? <Navigate to="/school-admin-dashboard" replace />
      : <Navigate to="/not-authorized" replace />),
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: PATHS.ADMISSIONS_START,
    element: <AdmissionsStartPage />,
  },
  {
    path: PATHS.PARENT_ADMISSIONS_START,
    element: <AdmissionsStartPage />,
  },
  {
    path: '/parent/admissions',
    element: <Navigate to={PATHS.PARENT_ADMISSIONS_START} replace />,
  },
  {
    path: PATHS.ADMISSIONS_APPLY,
    element: <ProspectiveFamilyAdmissionsWizard />,
  },
  {
    path: PATHS.ADMISSIONS_CHECKLIST,
    element: <AdmissionsChecklistHubPage />,
  },
  {
    path: PATHS.APPLY,
    element: <Navigate to={PATHS.ADMISSIONS_START} replace />,
  },
  {
    path: '/logout',
    element: <LogoutPage />,
  },
  {
    // Unified role dashboard � /dash/admin, /dash/teacher, /dash/parent, etc.
    path: PATHS.ROLE_DASHBOARD,
    element: <RoleDashboardPage />,
  },
  {
    path: '/teacher/attendance',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <TeacherAttendancePage />
      </RoleGuard>
    ),
  },
  {
    path: '/parent/attendance',
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentAttendancePage />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/parent/crownpass',
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <CrownPassMyTicketsPage />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/crownpass/scan',
    element: (
      <RoleGuard allowedRoles={CROWNPASS_SCANNER_ROLES}>
        <CrownPassScannerPage />
      </RoleGuard>
    ),
  },
  {
    path: '/operations/online-learning-command',
    element: (
      <RoleGuard allowedRoles={LEARNING_COMMAND_ALLOWED_ROLES}>
        <OnlineLearningCommandCenter />
      </RoleGuard>
    ),
  },
  {
    path: '/teacher/daily-cockpit',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <TeacherDailyCockpitPage />
      </RoleGuard>
    ),
  },
  {
    path: '/teacher/lesson-plans/today',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <TeacherDailyCockpitPage />
      </RoleGuard>
    ),
  },
  {
    path: '/parent/learning-status',
    element: (
      <RoleGuard allowedRoles={STUDENT_LEARNING_ALLOWED_ROLES}>
        <ParentLearningStatusPage />
      </RoleGuard>
    ),
  },
  {
    path: '/student/today',
    element: (
      <RoleGuard allowedRoles={STUDENT_LEARNING_ALLOWED_ROLES}>
        <StudentTodayPage />
      </RoleGuard>
    ),
  },
  {
    path: '/student/assignments',
    element: (
      <RoleGuard allowedRoles={STUDENT_LEARNING_ALLOWED_ROLES}>
        <StudentTodayPage />
      </RoleGuard>
    ),
  },
  {
    path: '/curriculum/import',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <CurriculumImportPage />
      </RoleGuard>
    ),
  },
  {
    path: '/integrations/microsoft-education/health',
    element: (
      <RoleGuard allowedRoles={MICROSOFT_EDUCATION_ALLOWED_ROLES}>
        <MicrosoftEducationHealthPage />
      </RoleGuard>
    ),
  },
  {
    path: '/academics/dual-enrollment',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <DualEnrollmentTrackerPage />
      </RoleGuard>
    ),
  },
  {
    path: '/academics/interventions',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <InterventionCoursesPage />
      </RoleGuard>
    ),
  },
  {
    path: '/academics/interventions/new',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <InterventionCoursesPage />
      </RoleGuard>
    ),
  },
  {
    path: PATHS.PARENT_BILLING,
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentJourneyRouteGuard stage="billing">
          <FinanceInvoicesList />
        </ParentJourneyRouteGuard>
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.PARENT_BILLING_PAY,
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentJourneyRouteGuard stage="billingPay">
          <ParentApplicationFeePaymentPage />
        </ParentJourneyRouteGuard>
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.PARENT_FINANCIAL_AID,
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentJourneyRouteGuard stage="aid">
          <ParentFinancialAidPreparationPage />
        </ParentJourneyRouteGuard>
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.PARENT_ADMISSIONS_STATUS,
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentJourneyRouteGuard stage="status">
          <ParentLifecycleStatusCenterPage />
        </ParentJourneyRouteGuard>
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.NOT_AUTHORIZED,
    element: <NotAuthorized />,
  },
  {
    path: PATHS.FORBIDDEN,
    element: <ForbiddenPage />,
  },
  // Legacy aliases used across cards/redirects until all links converge on canonical paths.
  {
    path: PATHS.BILLING,
    element: (
      <RequirePermission permission={APP_PERMISSIONS.BILLING_VIEW}>
        <BillingDashboard />
      </RequirePermission>
    ),
  },
  {
    path: PATHS.BILLING_DASHBOARD,
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <BillingDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    // Alias: /billing/dashboard mirrors /billing for inbound nav links
    path: '/billing/dashboard',
    element: (
      <RequirePermission permission={APP_PERMISSIONS.BILLING_VIEW}>
        <BillingDashboard />
      </RequirePermission>
    ),
  },
  {
    path: PATHS.FINANCIAL_AID,
    element: (
      <RoleRouteGuard allowedRoles={FINANCIAL_AID_ALLOWED_ROLES}>
        <FinancialAidDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.ATTENDANCE,
    element: (IS_LAUNCH_PREVIEW
      ? <CrownLaunchModulePage moduleKey="attendance" activePath="/attendance" />
      : <Navigate to={PATHS.TEACHER_ATTENDANCE} replace />),
  },
  // Contract-preserving teacher alias routes.
  // Keep these as literal strings in router.jsx for static gate checks.
  {
    path: '/teacher/gradebook',
    element: <Navigate to="/gradebook" replace />,
  },
  {
    path: '/teacher/communications',
    element: <Navigate to="/communications-dashboard" replace />,
  },
  {
    path: '/teacher/scheduling',
    element: <Navigate to="/scheduling-dashboard" replace />,
  },
  {
    path: '/teacher',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <TeacherDashboard />
      </RoleGuard>
    ),
  },
  {
    path: '/teacher/dashboard',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <TeacherDashboard />
      </RoleGuard>
    ),
  },
  {
    path: '/teacher/classes',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <ClassroomsDashboard />
      </RoleGuard>
    ),
  },
  {
    path: '/teacher/lesson-plans',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <ClassroomsDashboard />
      </RoleGuard>
    ),
  },
  {
    path: '/teacher/curriculum',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <CurriculumPDDashboard />
      </RoleGuard>
    ),
  },
  {
    path: '/teacher/calendar-assignments',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <SchedulingDashboard />
      </RoleGuard>
    ),
  },
  // Contract-preserving parent alias routes.
  // Keep these as literal strings in router.jsx for static gate checks.
  {
    path: '/parent/communications',
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <Navigate to="/communications-dashboard" replace />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/parent/schedule',
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <Navigate to="/scheduling-dashboard" replace />
      </RoleRouteGuard>
    ),
  },
  ...dashboardRoutes,
  {
    path: PATHS.ACADEMICS,
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <AcademicsDashboard />
      </RoleGuard>
    ),
  },
  {
    path: '/parent',
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/parent/dashboard',
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.STUDENT,
    element: (
      <RoleRouteGuard allowedRoles={["student"]}>
        <StudentDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/student/dashboard',
    element: (
      <RoleRouteGuard allowedRoles={["student"]}>
        <StudentDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.CLASSROOMS,
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentJourneyRouteGuard stage="classAssignment">
          <ClassroomsDashboard />
        </ParentJourneyRouteGuard>
      </RoleRouteGuard>
    ),
  },
  {
    path: '/gradebook',
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <GradebookRO />
      </RoleGuard>
    ),
  },
  {
    path: PATHS.GRADEBOOK_SECTION,
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <GradebookRO />
      </RoleGuard>
    ),
  },
  {
    path: PATHS.TRANSCRIPT,
    element: (
      <RoleGuard allowedRoles={[...ROLE_GROUPS.ACADEMIC_TEAM, ...ROLE_GROUPS.FAMILY_VIEW]}>
        <TranscriptRO />
      </RoleGuard>
    ),
  },
  {
    path: PATHS.CATEGORY_WEIGHTS,
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <CategoryWeightsEditor />
      </RoleGuard>
    ),
  },
  {
    path: PATHS.ADMISSIONS,
    element: (IS_LAUNCH_PREVIEW
      ? <CrownLaunchModulePage moduleKey="admissions" activePath="/admissions" />
      : <AdmissionsPipelineList />),
  },
  {
    path: '/admissions/dashboard',
    element: (IS_LAUNCH_PREVIEW
      ? <CrownLaunchModulePage moduleKey="admissions" activePath="/admissions" />
      : <AdmissionsPipelineList />),
  },
  {
    path: PATHS.ADMISSIONS_PIPELINE,
    element: <AdmissionsPipelineList />,
  },
  // Wizard Hub � lists all registered wizards from /api/v1/wizards/
  {
    path: PATHS.WIZARDS,
    element: <WizardHub />,
  },
  // Wizard routes are owned by routes/wizards.js.
  ...wizardRoutes(),
  {
    path: PATHS.FINANCE_INVOICES,
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <FinanceInvoicesList />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.MY_FORMS,
    element: <MyElectronicFormsPage />,
  },
  {
    path: PATHS.COMMUNICATIONS,
    element: (IS_LAUNCH_PREVIEW
      ? <CrownLaunchModulePage moduleKey="communications" activePath="/communications" />
      : <CommunicationsThreadsList />),
  },
  {
    path: PATHS.SERVICE_HOURS,
    element: <ServiceHoursPage />,
  },
  {
    path: PATHS.ACADEMICS_TEACHER_GRADING,
    element: (
      <RoleGuard allowedRoles={ROLE_GROUPS.ACADEMIC_TEAM}>
        <AcademicsTeacherGrading />
      </RoleGuard>
    ),
  },
  {
    path: PATHS.ACADEMICS_STUDENT_WORK,
    element: (
      <RoleGuard allowedRoles={[...ROLE_GROUPS.ACADEMIC_TEAM, ...ROLE_GROUPS.FAMILY_VIEW]}>
        <AcademicsStudentWork />
      </RoleGuard>
    ),
  },
  {
    path: PATHS.ACADEMICS_PARENT_SNAPSHOT,
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentJourneyRouteGuard stage="activeStudent">
          <AcademicsParentSnapshot />
        </ParentJourneyRouteGuard>
      </RoleRouteGuard>
    ),
  },
  {
    path: '/students/:id',
    element: <Student360Page />,
  },
  {
    path: '/parent/students/:id',
    element: (
      <RoleRouteGuard allowedRoles={["parent"]}>
        <ParentJourneyRouteGuard stage="activeStudent">
          <ParentStudent360Page />
        </ParentJourneyRouteGuard>
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.REPORTING,
    element: (
      <RequirePermission permission={APP_PERMISSIONS.REPORTING_VIEW}>
        <IntegrityDashboard />
      </RequirePermission>
    ),
  },
  {
    path: '/admin',
    element: <Navigate to="/school-admin-dashboard" replace />,
  },
  {
    path: '/admin/dashboard',
    element: <Navigate to="/school-admin-dashboard" replace />,
  },
  {
    path: '/school-admin-dashboard',
    element: (
      <RoleRouteGuard allowedRoles={ROLE_GROUPS.ADMIN_ONLY}>
        <SchoolAdministratorDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/school-admin',
    element: (
      <RoleRouteGuard allowedRoles={ROLE_GROUPS.ADMIN_ONLY}>
        <SchoolAdministratorDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/school-administrator',
    element: (
      <RoleRouteGuard allowedRoles={ROLE_GROUPS.ADMIN_ONLY}>
        <SchoolAdministratorDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.BOARD,
    element: <BoardDashboard />,
  },
  {
    path: PATHS.FINANCE,
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        {IS_LAUNCH_PREVIEW
          ? <CrownLaunchModulePage moduleKey="finance" activePath="/finance" />
          : <FinanceDashboard />}
      </RoleRouteGuard>
    ),
  },
  {
    path: '/finance/dashboard',
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        {IS_LAUNCH_PREVIEW
          ? <CrownLaunchModulePage moduleKey="finance" activePath="/finance" />
          : <FinanceDashboard />}
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.IT,
    element: <ITDashboard />,
  },
  {
    path: PATHS.MARKETING,
    element: <MarketingDashboard />,
  },
  {
    path: PATHS.SPIRITUAL_LIFE,
    element: <SpiritualLifeDashboard />,
  },
  {
    path: PATHS.MASTER_CONTROL,
    element: <AdminDashboard />,
  },
  {
    path: PATHS.OFFICE,
    element: <OfficeDashboard />,
  },
  {
    path: PATHS.HEALTH,
    element: <HealthDashboard />,
  },
  {
    path: PATHS.COUNSELING,
    element: <CounselingDashboard />,
  },
  {
    path: PATHS.FOOD,
    element: <FoodDashboard />,
  },
  {
    path: PATHS.ATHLETICS,
    element: <AthleticsDashboard />,
  },
  {
    path: PATHS.SYSTEM_STATUS,
    element: (
      <RequirePermission permission={APP_PERMISSIONS.SYSTEM_VIEW}>
        <SystemStatusPage />
      </RequirePermission>
    ),
  },
  {
    path: PATHS.RELEASE_READINESS,
    element: (
      <RequirePermission permission={APP_PERMISSIONS.RELEASE_VIEW}>
        <ReleaseReadinessPage />
      </RequirePermission>
    ),
  },
  {
    path: PATHS.DEMO_READINESS,
    element: (
      <RequirePermission permission={APP_PERMISSIONS.DEMO_VIEW}>
        <DemoReadinessPage />
      </RequirePermission>
    ),
  },
  {
    path: PATHS.ADVANCEMENT,
    element: <AdvancementDashboard />,
  },
  {
    path: PATHS.TRANSPORTATION,
    element: <TransportationDashboard />,
  },
  {
    path: PATHS.FACILITIES,
    element: <FacilitiesDashboard />,
  },
  {
    path: PATHS.SECURITY,
    element: <SecurityDashboard />,
  },
  {
    path: PATHS.ACADEMIC_SUPPORT,
    element: <AcademicSupportDashboard />,
  },
  {
    path: PATHS.FINE_ARTS,
    element: <FineArtsDashboard />,
  },
  {
    path: PATHS.LIBRARY,
    element: <LibraryDashboard />,
  },
  {
    path: PATHS.EXTENDED_CARE,
    element: <ExtendedCareDashboard />,
  },
  {
    path: PATHS.SUMMER_CAMP_ROSTER,
    element: (
      <RoleRouteGuard allowedRoles={ROLE_GROUPS.SUMMER_CAMP_TEAM}>
        <SummerCampRosterPage />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.SUMMER_CAMP_SETUP,
    element: (
      <RoleRouteGuard allowedRoles={ROLE_GROUPS.SUMMER_CAMP_TEAM}>
        <SummerCampSetupWizard />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.REGISTRAR,
    element: <RegistrarDashboard />,
  },
  {
    path: PATHS.COMMUNICATIONS_DIRECTOR,
    element: <CommunicationsDirectorDashboard />,
  },
  {
    path: PATHS.PD,
    element: <PDDashboard />,
  },
  {
    path: PATHS.STUDENT_SERVICES,
    element: <StudentServicesDashboard />,
  },
  {
    path: PATHS.HR,
    element: <HumanResources />,
  },
  {
    path: PATHS.SAFETY,
    element: <SafetyDashboard />,
  },
  {
    path: PATHS.BOARD_EXECUTIVE,
    element: <BoardExecutiveDashboard />,
  },
  {
    path: PATHS.AFTERCARE_ROSTER,
    element: <AftercareRosterPage />,
  },
  {
    path: PATHS.WIZARD_AFTERCARE_SETUP,
    element: <AftercareSetupWizard />,
  },
  {
    path: PATHS.WIZARD_FINANCE_SETUP,
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <FinanceSetupWizard />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.FINANCE_FAMILY_ACCOUNT,
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <FamilyAccountDetail />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.FINANCE_PAYMENT_METHODS,
    element: (
      <RoleRouteGuard
        allowedRoles={[
          "super_admin",
          "school_admin",
          "finance_admin",
          "parent",
        ]}
      >
        <SavedPaymentMethodsPage />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.FINANCE_EXPORTS,
    element: (
      <RoleRouteGuard
        allowedRoles={[
          "super_admin",
          "school_admin",
          "finance_admin",
          "parent",
        ]}
      >
        <FamilyStatementExportPage />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.FINANCE_EXCEPTIONS,
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <PaymentExceptionsQueue />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.NOT_FOUND,
    element: <NotFoundPage />,
  },
  // ── CROWN sidebar navigation routes ──────────────────────────────────
  {
    path: PATHS.STUDENT_LIFE,
    element: IS_LAUNCH_PREVIEW
      ? <StudentDashboard />
      : <SpiritualLifeDashboard />,
  },
  {
    path: PATHS.SETTINGS,
    element: IS_LAUNCH_PREVIEW
      ? <SchoolSettingsPage />
      : <AdminDashboard />,
  },
  // ── Common inbound path aliases (no-backend fallback redirects) ──────────
  { path: '/students', element: <Navigate to={PATHS.ADMISSIONS} replace /> },
  { path: '/families', element: <Navigate to={PATHS.SCHOOL_ADMIN} replace /> },
  { path: '/staff', element: <Navigate to={PATHS.STAFF} replace /> },
  { path: '/reports', element: <Navigate to={PATHS.REPORTING} replace /> },
  { path: '/enrollment', element: <Navigate to={PATHS.ENROLLMENT} replace /> },
], {
  future: {
    v7_startTransition: true,
  },
});
