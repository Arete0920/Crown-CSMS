import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import './styles/crown-theme.css';
import './styles/crown.css';
import './styles/launch-shell.css';
import { crownTheme } from './theme/crownTheme';
import { router } from './routes/router.jsx';
import { AutoLoginGate } from './components/AutoLoginGate.jsx';
import AuthProvider from './auth/AuthProvider.jsx';
import AppErrorBoundary from './components/system/AppErrorBoundary.jsx';
import StartupGuard from './components/system/StartupGuard.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider theme={crownTheme}>
      <CssBaseline enableColorScheme />
      <AuthProvider>
        <AutoLoginGate>
          <StartupGuard>
            <AppErrorBoundary>
              <RouterProvider router={router} />
            </AppErrorBoundary>
          </StartupGuard>
        </AutoLoginGate>
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
);
