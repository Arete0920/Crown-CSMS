import { createBrowserRouter, Navigate } from "react-router-dom";

// No-op touch to ensure required route/dashboard gate contexts run on this PR.

import RoleDashboardPage from "../pages/RoleDashboardPage.jsx";
import { BillingDashboard } from "../pages/BillingDashboard.jsx";
import { FinancialAidDashboard } from "../pages/FinancialAidDashboard.jsx";
import { AcademicsDashboard } from "../pages/AcademicsDashboard.jsx";
import { GradebookRO } from "../pages/GradebookRO.jsx";
import { TranscriptRO } from "../pages/TranscriptRO.jsx";
import { CategoryWeightsEditor } from "../pages/CategoryWeightsEditor.jsx";
import { AdmissionsPipelineList } from "../pages/AdmissionsPipelineList.jsx";
import FinanceInvoicesList from "../pages/FinanceInvoicesList.jsx";
import CommunicationsThreadsList from "../pages/CommunicationsThreadsList.jsx";
import ClassroomsDashboard from "../pages/ClassroomsDashboard.jsx";
import ServiceHoursPage from "../pages/ServiceHoursPage.jsx";
import Student360Page from "../pages/Student360Page.jsx";
import ParentStudent360Page from "../pages/ParentStudent360Page.jsx";
import AcademicsTeacherGrading from "../pages/AcademicsTeacherGrading.jsx";
import AcademicsStudentWork from "../pages/AcademicsStudentWork.jsx";
import AcademicsParentSnapshot from "../pages/AcademicsParentSnapshot.jsx";
import TeacherDashboard from "../pages/TeacherDashboard.jsx";
import ParentDashboard from "../pages/ParentDashboard.jsx";
import StudentDashboard from "../pages/StudentDashboard.jsx";
import RoleHomeRedirect from "../pages/RoleHomeRedirect.jsx";
import TeacherAttendancePage from "../pages/TeacherAttendancePage.jsx";
import ParentAttendancePage from "../pages/ParentAttendancePage.jsx";
import AttendanceDashboard from "../pages/AttendanceDashboard.jsx";
import LoginPage from "../pages/LoginPage.jsx";
import LogoutPage from "../pages/LogoutPage.jsx";
import IntegrityDashboard from "../pages/IntegrityDashboard.jsx";
import AdminDashboard from "../pages/AdminDashboard.jsx";
import AdminCommandCenterClean from "../pages/AdminCommandCenterClean.jsx";
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
import AdvancementDashboard from "../pages/AdvancementDashboard.jsx";
import TransportationDashboard from "../pages/TransportationDashboard.jsx";
import FacilitiesDashboard from "../pages/FacilitiesDashboard.jsx";
import SecurityDashboard from "../pages/SecurityDashboard.jsx";
import AcademicSupportDashboard from "../pages/AcademicSupportDashboard.jsx";
import FineArtsDashboard from "../pages/FineArtsDashboard.jsx";
import LibraryDashboard from "../pages/LibraryDashboard.jsx";
import ExtendedCareDashboard from "../pages/ExtendedCareDashboard.jsx";
import RegistrarDashboard from "../pages/RegistrarDashboard.jsx";
import CommunicationsDirectorDashboard from "../pages/CommunicationsDirectorDashboard.jsx";
import PDDashboard from "../pages/PDDashboard.jsx";
import StudentServicesDashboard from "../pages/StudentServicesDashboard.jsx";
import HumanResources from "../pages/HumanResources.jsx";
import SafetyDashboard from "../pages/SafetyDashboard.jsx";
import BoardExecutiveDashboard from "../pages/BoardExecutiveDashboard.jsx";
import AftercareRosterPage from "../pages/AftercareRosterPage.jsx";
import AftercareSetupWizard from "../pages/wizards/AftercareSetupWizard.jsx";
import FinanceSetupWizard from "../pages/wizards/FinanceSetupWizard.jsx";
import NotAuthorized from "../pages/NotAuthorized.jsx";
import RoleRouteGuard from "../components/routing/RoleRouteGuard.jsx";
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
import { dashboardRoutes } from "./dashboardRoutes";
import { wizardRoutes } from "./wizards.js";
import { PATHS } from "./paths";
import { ROLE_GROUPS } from "./routeGroups";
import WizardHub from "../pages/WizardHub.jsx";
import CompuwerxTestCheckout from "../pages/CompuwerxTestCheckout.jsx";
import FamilyAccountDetail from "../pages/FamilyAccountDetail.jsx";
import CompuwerxDisputesDashboard from "../pages/CompuwerxDisputesDashboard.jsx";
import CompuwerxPayoutReconciliation from "../pages/CompuwerxPayoutReconciliation.jsx";
import SavedPaymentMethodsPage from "../pages/SavedPaymentMethodsPage.jsx";
import FamilyStatementExportPage from "../pages/FamilyStatementExportPage.jsx";
import CompuwerxDisputeWorkbench from "../pages/CompuwerxDisputeWorkbench.jsx";
import PaymentExceptionsQueue from "../pages/PaymentExceptionsQueue.jsx";
import CompuwerxBankReconciliation from "../pages/CompuwerxBankReconciliation.jsx";

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

const IS_SANDBOX = Boolean(import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1");
const IS_LAUNCH_PREVIEW = Boolean(import.meta.env.DEV || IS_SANDBOX || import.meta.env.VITE_LAUNCH_UI_TAKEOVER === '1');

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RoleHomeRedirect />,
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
    path: '/logout',
    element: <LogoutPage />,
  },
  {
    // Unified role dashboard � /dash/admin, /dash/teacher, /dash/parent, etc.
    path: PATHS.ROLE_DASHBOARD,
    element: <RoleDashboardPage />,
  },
  {
    path: PATHS.TEACHER_ATTENDANCE,
    element: <TeacherAttendancePage />,
  },
  {
    path: PATHS.PARENT_ATTENDANCE,
    element: <ParentAttendancePage />,
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
    path: '/teacher/attendance',
    element: <AttendanceDashboard />,
  },
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
    element: <TeacherDashboard />,
  },
  // Contract-preserving parent alias routes.
  // Keep these as literal strings in router.jsx for static gate checks.
  {
    path: '/parent/attendance',
    element: <AttendanceDashboard />,
  },
  {
    path: '/parent/communications',
    element: <Navigate to="/communications-dashboard" replace />,
  },
  {
    path: '/parent/schedule',
    element: <Navigate to="/scheduling-dashboard" replace />,
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
    element: <ParentDashboard />,
  },
  {
    path: PATHS.STUDENT,
    element: <StudentDashboard />,
  },
  {
    path: PATHS.CLASSROOMS,
    element: <ClassroomsDashboard />,
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
      <RoleGuard allowedRoles={ROLE_GROUPS.FAMILY_VIEW}>
        <AcademicsParentSnapshot />
      </RoleGuard>
    ),
  },
  {
    path: '/students/:id',
    element: <Student360Page />,
  },
  {
    path: '/parent/students/:id',
    element: <ParentStudent360Page />,
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
    element: (
      <RoleRouteGuard allowedRoles={ROLE_GROUPS.ADMIN_ONLY}>
        <AdminCommandCenterClean />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/school-admin',
    element: (
      <RoleRouteGuard allowedRoles={ROLE_GROUPS.ADMIN_ONLY}>
        <AdminCommandCenterClean />
      </RoleRouteGuard>
    ),
  },
  {
    path: '/school-administrator',
    element: (
      <RoleRouteGuard allowedRoles={ROLE_GROUPS.ADMIN_ONLY}>
        <AdminCommandCenterClean />
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
          : (
          <FinanceDashboard />
          )}
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
    path: PATHS.FINANCE_COMPUWERX_TEST,
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <CompuwerxTestCheckout />
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
    path: PATHS.FINANCE_DISPUTES,
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <CompuwerxDisputesDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.FINANCE_PAYOUT_RECONCILIATION,
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <CompuwerxPayoutReconciliation />
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
    path: PATHS.FINANCE_DISPUTE_WORKBENCH,
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <CompuwerxDisputeWorkbench />
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
    path: PATHS.FINANCE_BANK_RECONCILIATION,
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <CompuwerxBankReconciliation />
      </RoleRouteGuard>
    ),
  },
  {
    path: PATHS.NOT_FOUND,
    element: <NotFoundPage />,
  },
  // ── CROWN sidebar navigation routes ──────────────────────────────────
  {
    path: PATHS.SCHOOL_ADMIN,
    element: <AdminCommandCenterClean />,
  },
  {
    path: PATHS.STUDENT_LIFE,
    element: IS_LAUNCH_PREVIEW
      ? <CrownLaunchModulePage moduleKey="student" activePath="/student-life" />
      : <SpiritualLifeDashboard />,
  },
  {
    path: PATHS.SETTINGS,
    element: IS_LAUNCH_PREVIEW
      ? <CrownLaunchModulePage moduleKey="schoolAdministrator" activePath="/settings" />
      : <AdminDashboard />,
  },
  {
    path: PATHS.REPORTING,
    element: <IntegrityDashboard />,
  },
]);
