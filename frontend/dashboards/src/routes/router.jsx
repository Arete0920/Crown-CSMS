import { createBrowserRouter } from 'react-router-dom';

import { BillingDashboard } from '../pages/BillingDashboard.jsx';
import { FinancialAidDashboard } from '../pages/FinancialAidDashboard.jsx';
import { AcademicsDashboard } from '../pages/AcademicsDashboard.jsx';
import { GradebookRO } from '../pages/GradebookRO.jsx';
import { TranscriptRO } from '../pages/TranscriptRO.jsx';
import { CategoryWeightsEditor } from '../pages/CategoryWeightsEditor.jsx';
import { AdmissionsPipelineList } from '../pages/AdmissionsPipelineList.jsx';
import FinanceInvoicesList from '../pages/FinanceInvoicesList.jsx';
import CommunicationsThreadsList from '../pages/CommunicationsThreadsList.jsx';
import OpsCommandCenter from '../components/OpsCommandCenter.jsx';
import ClassroomsDashboard from '../pages/ClassroomsDashboard.jsx';
import DisciplinePage from '../pages/DisciplinePage.jsx';
import ServiceHoursPage from '../pages/ServiceHoursPage.jsx';
import TeamsPreviewPage from '../pages/TeamsPreviewPage.jsx';
import CommsInboxPage from '../pages/CommsInboxPage.jsx';
import CommsThreadPage from '../pages/CommsThreadPage.jsx';
import CommsComposePage from '../pages/CommsComposePage.jsx';
import Student360Page from '../pages/Student360Page.jsx';
import ParentStudent360Page from '../pages/ParentStudent360Page.jsx';
import AcademicsTeacherGrading from '../pages/AcademicsTeacherGrading.jsx';
import AcademicsStudentWork from '../pages/AcademicsStudentWork.jsx';
import AcademicsParentSnapshot from '../pages/AcademicsParentSnapshot.jsx';
import TeacherDashboard from '../pages/TeacherDashboard.jsx';
import ParentDashboard from '../pages/ParentDashboard.jsx';
import StudentDashboard from '../pages/StudentDashboard.jsx';
import RoleHomeRedirect from '../pages/RoleHomeRedirect.jsx';
import TeacherAttendancePage from '../pages/TeacherAttendancePage.jsx';
import ParentAttendancePage from '../pages/ParentAttendancePage.jsx';
import { LoginPage } from '../pages/LoginPage.jsx';
import IntegrityDashboard from '../pages/IntegrityDashboard.jsx';
import AdminDashboard from '../pages/AdminDashboard.jsx';
import BoardDashboard from '../pages/BoardDashboard.jsx';
import FinanceDashboard from '../pages/FinanceDashboard.jsx';
import ITDashboard from '../pages/ITDashboard.jsx';
import MarketingDashboard from '../pages/MarketingDashboard.jsx';
import SpiritualLifeDashboard from '../pages/SpiritualLifeDashboard.jsx';
import OfficeDashboard from '../pages/OfficeDashboard.jsx';
import HealthDashboard from '../pages/HealthDashboard.jsx';
import CounselingDashboard from '../pages/CounselingDashboard.jsx';
import FoodDashboard from '../pages/FoodDashboard.jsx';
import AthleticsDashboard from '../pages/AthleticsDashboard.jsx';
import AdvancementDashboard from '../pages/AdvancementDashboard.jsx';
import TransportationDashboard from '../pages/TransportationDashboard.jsx';
import FacilitiesDashboard from '../pages/FacilitiesDashboard.jsx';
import SecurityDashboard from '../pages/SecurityDashboard.jsx';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/teacher/attendance',
    element: <TeacherAttendancePage />,
  },
  {
    path: '/parent/attendance',
    element: <ParentAttendancePage />,
  },
  {
    path: '/',
    element: <RoleHomeRedirect />,
  },
  {
    path: '/billing',
    element: <BillingDashboard />,
  },
  {
    path: '/financial-aid',
    element: <FinancialAidDashboard />,
  },
  {
    path: '/academics',
    element: <AcademicsDashboard />,
  },
  {
    path: '/teacher',
    element: <TeacherDashboard />,
  },
  {
    path: '/parent',
    element: <ParentDashboard />,
  },
  {
    path: '/student',
    element: <StudentDashboard />,
  },
  {
    path: '/classrooms',
    element: <ClassroomsDashboard />,
  },
  {
    path: '/gradebook',
    element: <GradebookRO />,
  },
  {
    path: '/gradebook/:sectionId',
    element: <GradebookRO />,
  },
  {
    path: '/transcript',
    element: <TranscriptRO />,
  },
  {
    path: '/category-weights',
    element: <CategoryWeightsEditor />,
  },
  {
    path: '/admissions',
    element: <AdmissionsPipelineList />,
  },
  {
    path: '/finance/invoices',
    element: <FinanceInvoicesList />,
  },
  {
    path: '/communications',
    element: <CommunicationsThreadsList />,
  },
  {
    path: '/ops',
    element: <OpsCommandCenter />,
  },
  {
    path: '/academics/teacher-grading',
    element: <AcademicsTeacherGrading />,
  },
  {
    path: '/academics/student-work',
    element: <AcademicsStudentWork />,
  },
  {
    path: '/academics/parent-snapshot',
    element: <AcademicsParentSnapshot />,
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
    path: '/integrity',
    element: <IntegrityDashboard />,
  },
  {
    path: '/admin',
    element: <AdminDashboard />,
  },
  {
    path: '/board',
    element: <BoardDashboard />,
  },
  {
    path: '/finance',
    element: <FinanceDashboard />,
  },
  {
    path: '/it',
    element: <ITDashboard />,
  },
  {
    path: '/marketing',
    element: <MarketingDashboard />,
  },
  {
    path: '/spiritual-life',
    element: <SpiritualLifeDashboard />,
  },
  {
    path: '/office',
    element: <OfficeDashboard />,
  },
  {
    path: '/health',
    element: <HealthDashboard />,
  },
  {
    path: '/counseling',
    element: <CounselingDashboard />,
  },
  {
    path: '/food',
    element: <FoodDashboard />,
  },
  {
    path: '/athletics',
    element: <AthleticsDashboard />,
  },
  {
    path: '/advancement',
    element: <AdvancementDashboard />,
  },
  {
    path: '/transportation',
    element: <TransportationDashboard />,
  },
  {
    path: '/facilities',
    element: <FacilitiesDashboard />,
  },
  {
    path: '/security',
    element: <SecurityDashboard />,
  },
]);



