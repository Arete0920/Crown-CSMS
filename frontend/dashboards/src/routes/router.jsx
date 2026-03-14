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
import OpsCommandCenter from "../components/OpsCommandCenter.jsx";
import ClassroomsDashboard from "../pages/ClassroomsDashboard.jsx";
import DisciplinePage from "../pages/DisciplinePage.jsx";
import ServiceHoursPage from "../pages/ServiceHoursPage.jsx";
import TeamsPreviewPage from "../pages/TeamsPreviewPage.jsx";
import CommsInboxPage from "../pages/CommsInboxPage.jsx";
import CommsThreadPage from "../pages/CommsThreadPage.jsx";
import CommsComposePage from "../pages/CommsComposePage.jsx";
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
import LoginPage from "../pages/LoginPage.jsx";
import IntegrityDashboard from "../pages/IntegrityDashboard.jsx";
import AdminDashboard from "../pages/AdminDashboard.jsx";
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
import AdmissionsIntakeWizard from "../pages/AdmissionsIntakeWizard.jsx";
import ReenrollmentWizard from "../pages/ReenrollmentWizard.jsx";
import FinancialAidWizard from "../pages/FinancialAidWizard.jsx";
import EnrollmentConversionWizard from "../pages/EnrollmentConversionWizard.jsx";
import EnrollmentPeriodWizard from "../pages/EnrollmentPeriodWizard.jsx";
import { dashboardRoutes } from "./dashboardRoutes";
import { wizardRoutes } from "./wizards.js";
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

const FINANCE_ALLOWED_ROLES = ["super_admin", "school_admin", "finance_admin"];

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RoleHomeRedirect />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    // Unified role dashboard — /dash/admin, /dash/teacher, /dash/parent, etc.
    path: "/dash/:role",
    element: <RoleDashboardPage />,
  },
  {
    path: "/teacher/attendance",
    element: <TeacherAttendancePage />,
  },
  {
    path: "/parent/attendance",
    element: <ParentAttendancePage />,
  },
  {
    path: "/not-authorized",
    element: <NotAuthorized />,
  },
  // Legacy aliases used across cards/redirects until all links converge on canonical paths.
  {
    path: "/billing",
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <BillingDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/billing-dashboard",
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <BillingDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/financial-aid",
    element: <Navigate to="/financial-aid-dashboard" replace />,
  },
  {
    path: "/attendance",
    element: <Navigate to="/teacher/attendance" replace />,
  },
  ...dashboardRoutes,
  {
    path: "/academics",
    element: <AcademicsDashboard />,
  },
  {
    path: "/teacher",
    element: <TeacherDashboard />,
  },
  {
    path: "/parent",
    element: <ParentDashboard />,
  },
  {
    path: "/student",
    element: <StudentDashboard />,
  },
  {
    path: "/classrooms",
    element: <ClassroomsDashboard />,
  },
  {
    path: "/gradebook",
    element: <GradebookRO />,
  },
  {
    path: "/gradebook/:sectionId",
    element: <GradebookRO />,
  },
  {
    path: "/transcript",
    element: <TranscriptRO />,
  },
  {
    path: "/category-weights",
    element: <CategoryWeightsEditor />,
  },
  {
    path: "/admissions",
    element: <AdmissionsPipelineList />,
  },
  {
    path: "/admissions/pipeline",
    element: <AdmissionsPipelineList />,
  },
  // Wizard Hub — lists all registered wizards from /api/v1/wizards/
  {
    path: "/wizards",
    element: <WizardHub />,
  },
  // Guarded admissions/enrollment wizard routes
  {
    path: "/onboarding",
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "admissions_manager"]}
      >
        <AdmissionsIntakeWizard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/reenrollment",
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "registrar"]}
      >
        <ReenrollmentWizard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/aid-setup",
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <FinancialAidWizard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/enrollment-conversion",
    element: (
      <RoleRouteGuard
        allowedRoles={[
          "super_admin",
          "school_admin",
          "admissions_manager",
          "registrar",
        ]}
      >
        <EnrollmentConversionWizard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/enrollment-period-setup",
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "registrar"]}
      >
        <EnrollmentPeriodWizard />
      </RoleRouteGuard>
    ),
  },
  // Keep all other setup wizards from the registry
  ...wizardRoutes().filter(
    (route) =>
      ![
        "/onboarding",
        "/reenrollment",
        "/aid-setup",
        "/enrollment-conversion",
        "/enrollment-period-setup",
      ].includes(route.path),
  ),
  {
    path: "/finance/invoices",
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <FinanceInvoicesList />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/communications",
    element: <CommunicationsThreadsList />,
  },
  {
    path: "/service-hours",
    element: <ServiceHoursPage />,
  },
  {
    path: "/ops",
    element: <OpsCommandCenter />,
  },
  {
    path: "/academics/teacher-grading",
    element: <AcademicsTeacherGrading />,
  },
  {
    path: "/academics/student-work",
    element: <AcademicsStudentWork />,
  },
  {
    path: "/academics/parent-snapshot",
    element: <AcademicsParentSnapshot />,
  },
  {
    path: "/students/:id",
    element: <Student360Page />,
  },
  {
    path: "/parent/students/:id",
    element: <ParentStudent360Page />,
  },
  {
    path: "/integrity",
    element: <IntegrityDashboard />,
  },
  {
    path: "/admin",
    element: <AdminDashboard />,
  },
  {
    path: "/board",
    element: <BoardDashboard />,
  },
  {
    path: "/finance",
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <FinanceDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/it",
    element: <ITDashboard />,
  },
  {
    path: "/marketing",
    element: <MarketingDashboard />,
  },
  {
    path: "/spiritual-life",
    element: <SpiritualLifeDashboard />,
  },
  {
    path: "/master-control",
    element: <AdminDashboard />,
  },
  {
    path: "/office",
    element: <OfficeDashboard />,
  },
  {
    path: "/health",
    element: <HealthDashboard />,
  },
  {
    path: "/counseling",
    element: <CounselingDashboard />,
  },
  {
    path: "/food",
    element: <FoodDashboard />,
  },
  {
    path: "/athletics",
    element: <AthleticsDashboard />,
  },
  {
    path: "/advancement",
    element: <AdvancementDashboard />,
  },
  {
    path: "/transportation",
    element: <TransportationDashboard />,
  },
  {
    path: "/facilities",
    element: <FacilitiesDashboard />,
  },
  {
    path: "/security",
    element: <SecurityDashboard />,
  },
  {
    path: "/academic-support",
    element: <AcademicSupportDashboard />,
  },
  {
    path: "/fine-arts",
    element: <FineArtsDashboard />,
  },
  {
    path: "/library",
    element: <LibraryDashboard />,
  },
  {
    path: "/extended-care",
    element: <ExtendedCareDashboard />,
  },
  {
    path: "/registrar",
    element: <RegistrarDashboard />,
  },
  {
    path: "/communications-director",
    element: <CommunicationsDirectorDashboard />,
  },
  {
    path: "/pd",
    element: <PDDashboard />,
  },
  {
    path: "/student-services",
    element: <StudentServicesDashboard />,
  },
  {
    path: "/hr",
    element: <HumanResources />,
  },
  {
    path: "/safety",
    element: <SafetyDashboard />,
  },
  {
    path: "/board/executive",
    element: <BoardExecutiveDashboard />,
  },
  {
    path: "/aftercare/roster",
    element: <AftercareRosterPage />,
  },
  {
    path: "/wizards/aftercare-setup",
    element: <AftercareSetupWizard />,
  },
  {
    path: "/wizards/finance-setup",
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <FinanceSetupWizard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/finance/compuwerx-test",
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <CompuwerxTestCheckout />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/finance/family-account",
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <FamilyAccountDetail />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/finance/disputes",
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <CompuwerxDisputesDashboard />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/finance/payout-reconciliation",
    element: (
      <RoleRouteGuard allowedRoles={FINANCE_ALLOWED_ROLES}>
        <CompuwerxPayoutReconciliation />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/finance/payment-methods",
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
    path: "/finance/exports",
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
    path: "/finance/dispute-workbench",
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <CompuwerxDisputeWorkbench />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/finance/exceptions",
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <PaymentExceptionsQueue />
      </RoleRouteGuard>
    ),
  },
  {
    path: "/finance/bank-reconciliation",
    element: (
      <RoleRouteGuard
        allowedRoles={["super_admin", "school_admin", "finance_admin"]}
      >
        <CompuwerxBankReconciliation />
      </RoleRouteGuard>
    ),
  },
]);
