import React from 'react';
import { createBrowserRouter } from 'react-router-dom';

import { HomeDashboard } from '../pages/HomeDashboard.jsx';
import { BillingDashboard } from '../pages/BillingDashboard.jsx';
import { FinancialAidDashboard } from '../pages/FinancialAidDashboard.jsx';

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
]);
