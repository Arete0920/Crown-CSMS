import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router/dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import './styles/crown-theme.css';
import './styles/crown.css';
import './styles/launch-shell.css';
import { crownTheme } from './theme/crownTheme';
import { router } from './routes/router.jsx';
import AuthProvider from './auth/AuthProvider.jsx';
import AppErrorBoundary from './components/system/AppErrorBoundary.jsx';
import StartupGuard from './components/system/StartupGuard.jsx';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('CROWN dashboard boot failed: missing #root element');
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <ThemeProvider theme={crownTheme}>
      <CssBaseline enableColorScheme />
      <AuthProvider>
        <StartupGuard>
          <AppErrorBoundary>
            <RouterProvider router={router} />
          </AppErrorBoundary>
        </StartupGuard>
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
);
