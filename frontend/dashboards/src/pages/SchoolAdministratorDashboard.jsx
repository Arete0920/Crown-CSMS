import ClassroomOperations from '../features/classroomExperience/ClassroomOperations.jsx';
import ClassroomWorkspace from '../features/classroomExperience/ClassroomWorkspace.jsx';
import { useEffect, useMemo, useState } from 'react';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import SandboxAdminTransactionPanel from '../components/admin/SandboxAdminTransactionPanel.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
import { loadSchoolAdministratorLiveSnapshot } from '../features/dashboards/dashboardApi';

function formatCount(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric < 0) {
    return '0';
  }

  return numeric.toLocaleString();
}

function cloneMetrics(metrics) {
  return Array.isArray(metrics) ? metrics.map((metric) => ({ ...metric })) : [];
}

function cloneCommandModules(commandModules) {
  return Array.isArray(commandModules)
    ? commandModules.map((module) => ({
      ...module,
      kpis: Array.isArray(module.kpis) ? module.kpis.map((kpi) => ({ ...kpi })) : [],
      details: Array.isArray(module.details) ? [...module.details] : [],
    }))
    : [];
}

function cloneDecisionPanel(decisionPanel) {
  if (!decisionPanel) {
    return null;
  }

  return {
    ...decisionPanel,
    actions: Array.isArray(decisionPanel.actions) ? decisionPanel.actions.map((action) => ({ ...action })) : [],
  };
}

function buildBaseConfig(baseConfig) {
  return {
    ...baseConfig,
    // Preserve the established route/navigation contract used by the release
    // proof while this page switches to its authoritative live-data lifecycle.
    dashboardTitle: 'School Administrator Dashboard',
    // This page already owns its authoritative live-data lifecycle through
    // loadSchoolAdministratorLiveSnapshot. Prevent CrownDashboardTemplate from
    // issuing a second obsolete role-specific summary request.
    disableLiveData: true,
    metrics: cloneMetrics(baseConfig.metrics),
    commandModules: cloneCommandModules(baseConfig.commandModules),
    decisionPanel: cloneDecisionPanel(baseConfig.decisionPanel),
  };
}

function applyFallbackSnapshot(config, snapshot) {
  return {
    ...config,
    dataState: snapshot?.dataState || 'fallback',
    sourceLabel: snapshot?.sourceLabel || config.sourceLabel,
    lastSyncLabel: snapshot?.lastSyncLabel || config.lastSyncLabel,
  };
}

function applyLiveDashboardMetrics(config, snapshot) {
  const widgetCount = Array.isArray(snapshot.dashboardSummary?.widgets) ? snapshot.dashboardSummary.widgets.length : 0;
  const alertCount = Array.isArray(snapshot.dashboardAlerts?.alerts) ? snapshot.dashboardAlerts.alerts.length : 0;
  const routeLabel = snapshot.dashboardMe?.default_route || '/dashboard';
  const roleCount = Array.isArray(snapshot.dashboardMe?.roles) ? snapshot.dashboardMe.roles.length : 0;

  if (config.metrics[0]) {
    config.metrics[0] = {
      ...config.metrics[0],
      value: formatCount(Math.max(widgetCount, 1)),
      detail: `Unified dashboard summary loaded from ${routeLabel}.`,
    };
  }

  if (config.metrics[1]) {
    config.metrics[1] = {
      ...config.metrics[1],
      value: formatCount(alertCount || roleCount),
      detail: alertCount ? 'Live alerts returned by /api/dashboards/alerts/.' : 'Live dashboard roles returned by /api/dashboards/me/.',
    };
  }

  if (config.metrics[2]) {
    config.metrics[2] = {
      ...config.metrics[2],
      value: roleCount > 0 ? 'Live access ready' : 'Access ready',
      detail: `Current default route resolved from live dashboard identity: ${routeLabel}.`,
    };
  }

  if (config.metrics[3]) {
    config.metrics[3] = {
      ...config.metrics[3],
      value: `${formatCount(widgetCount + alertCount)} signals`,
      detail: `${widgetCount} widgets and ${alertCount} alerts returned from live dashboard APIs.`,
    };
  }

  return {
    widgetCount,
    alertCount,
    routeLabel,
    roleCount,
    config,
    snapshot,
  };
}

function applyLiveDashboardDecisionPanel(config, context) {
  if (!config.decisionPanel) {
    return config;
  }

  const { widgetCount, alertCount, routeLabel, roleCount } = context;
  const liveDecisionCount = widgetCount + alertCount + roleCount;

  return {
    ...config,
    decisionPanel: {
      ...config.decisionPanel,
      primaryMetric: formatCount(liveDecisionCount),
      primaryMetricLabel: 'live dashboard signals',
      summary: `Live route ${routeLabel} with ${widgetCount} widgets and ${alertCount} alerts.`,
      actions: Array.isArray(config.decisionPanel.actions)
        ? config.decisionPanel.actions.map((action, index) => {
            if (index === 0) {
              return {
                ...action,
                value: formatCount(widgetCount || 1),
                detail: 'Live dashboard summary returned by /api/dashboards/summary/.',
              };
            }

            if (index === 2) {
              return {
                ...action,
                value: formatCount(alertCount),
                detail: 'Live alerts returned by /api/dashboards/alerts/.',
              };
            }

            return action;
          })
        : config.decisionPanel.actions,
    },
  };
}

function applyLiveDashboardCommandModules(config, context) {
  const { widgetCount, alertCount, routeLabel, roleCount, snapshot } = context;

  const nextConfig = { ...config };

  if (nextConfig.commandModules[0]) {
    nextConfig.commandModules[0] = {
      ...nextConfig.commandModules[0],
      mainKpi: `${formatCount(widgetCount || 1)} live widgets`,
      summary: `Live dashboard summary route ${routeLabel}.`,
      kpis: [
        { label: 'Widgets', value: formatCount(widgetCount) },
        { label: 'Alerts', value: formatCount(alertCount) },
        { label: 'Roles', value: formatCount(roleCount) },
        { label: 'Route', value: routeLabel },
      ],
      details: [
        'Dashboard identity loaded from /api/dashboards/me/.',
        `Summary widgets: ${widgetCount}`,
        `Alert count: ${alertCount}`,
      ],
      lastUpdated: snapshot.lastSyncLabel,
    };
  }

  if (nextConfig.commandModules[3]) {
    nextConfig.commandModules[3] = {
      ...nextConfig.commandModules[3],
      mainKpi: `${formatCount(alertCount)} live alerts`,
      summary: 'Live alert feed is sourced from the dashboard alerts endpoint.',
      kpis: [
        { label: 'Alerts', value: formatCount(alertCount) },
        { label: 'Widgets', value: formatCount(widgetCount) },
        { label: 'Roles', value: formatCount(roleCount) },
        { label: 'Live source', value: 'Yes' },
      ],
      details: [
        `Dashboard summary route: ${routeLabel}`,
        'Live summary and alert feeds are available for this session.',
      ],
      lastUpdated: snapshot.lastSyncLabel,
    };
  }

  return nextConfig;
}

function buildLiveConfig(baseConfig, snapshot) {
  const config = buildBaseConfig(baseConfig);

  if (!snapshot?.dashboardSummary && !snapshot?.dashboardMe && !snapshot?.dashboardAlerts) {
    return applyFallbackSnapshot(config, snapshot);
  }

  const liveContext = applyLiveDashboardMetrics(config, snapshot);

  return {
    ...applyLiveDashboardDecisionPanel(applyLiveDashboardCommandModules(liveContext.config, liveContext), liveContext),
    dataState: snapshot.dataState,
    sourceLabel: snapshot.sourceLabel,
    lastSyncLabel: snapshot.lastSyncLabel,
    updatesCount: Math.max(liveContext.widgetCount + liveContext.alertCount, config.updatesCount || 0),
  };
}

export default function SchoolAdministratorDashboard() {
  const baseConfig = useMemo(() => getDashboardTemplate('schoolAdministrator'), []);
  const [snapshot, setSnapshot] = useState({
    dataState: 'fallback',
    sourceLabel: baseConfig.sourceLabel || 'Dashboard template data',
    lastSyncLabel: baseConfig.lastSyncLabel || 'Using configured fallback data',
    dashboardMe: null,
    dashboardSummary: null,
    dashboardAlerts: null,
  });

  useEffect(() => {
    let active = true;

    loadSchoolAdministratorLiveSnapshot().then((nextSnapshot) => {
      if (active) {
        setSnapshot(nextSnapshot);
      }
    });

    return () => {
      active = false;
    };
  }, []);

  const config = useMemo(
    () => buildLiveConfig(baseConfig, snapshot),
    [baseConfig, snapshot],
  );

  return (
    <>
      <ClassroomOperations audience="admin" /><ClassroomWorkspace audience="admin" />
      <SandboxAdminTransactionPanel />
      <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />
    </>
  );
}
