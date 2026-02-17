import { createBrowserRouter } from 'react-router-dom';

import { HomeDashboard } from '../pages/HomeDashboard.jsx';
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

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomeDashboard />,
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
]);



