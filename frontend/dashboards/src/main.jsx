import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';

import './styles/crown-theme.css';
import './styles/crown.css';
import { router } from './routes/router.jsx';
import DevJwtPanel from './components/DevJwtPanel.jsx';
import { AutoLoginGate } from './components/AutoLoginGate.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AutoLoginGate>
      <RouterProvider router={router} />
      <DevJwtPanel />
    </AutoLoginGate>
  </React.StrictMode>
);
