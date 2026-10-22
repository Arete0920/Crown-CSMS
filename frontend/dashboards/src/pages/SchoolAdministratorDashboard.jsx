import ClassroomLeadership from '../features/classroomExperience/ClassroomLeadership.jsx';
import ClassroomOperations from '../features/classroomExperience/ClassroomOperations.jsx';
import ClassroomWorkspace from '../features/classroomExperience/ClassroomWorkspace.jsx';
import { useEffect, useMemo, useState } from 'react';
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import SandboxAdminTransactionPanel from '../components/admin/SandboxAdminTransactionPanel.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';
import { loadSchoolAdministratorLiveSnapshot } from '../features/dashboards/dashboardApi';

const ADMIN_SAMPLE_SOURCE = 'Illustrative Heritage school scenario — business figures are sample data, not live school records';

function buildAdministratorDemoConfig(baseConfig, snapshot) {
  // Infrastructure responses do not validate school business totals in the template.
  const connectionState = snapshot?.serviceState || 'checking';
  const responding = Number.isInteger(snapshot?.successfulEndpointCount)
    ? Math.max(0, Math.min(3, snapshot.successfulEndpointCount))
    : 0;
  const connectionDetail = connectionState === 'checking'
    ? 'checking dashboard API connectivity'
    : (connectionState === 'unavailable'
      ? 'dashboard APIs unavailable'
      : responding + ' of 3 dashboard API endpoints responded with valid school-scoped data');

  return {
    ...baseConfig,
    dashboardTitle: 'School Administrator Dashboard — Illustrative Scenario',
    disableLiveData: true,
    dataSource: 'sample',
    dataState: 'sample',
    sourceLabel: ADMIN_SAMPLE_SOURCE,
    lastSyncLabel: 'Illustrative scenario — no verified business-data synchronization',
    note: 'Sample demonstration only: enrollment, attendance, finance, staffing, alerts, trends, calendar items, decisions and activity are fictional examples. Dashboard service status: ' + connectionDetail + '. API connectivity does not certify these business figures.',
    metrics: (baseConfig.metrics || []).map((metric) => ({
      ...metric,
      dataState: 'sample',
      sourceLabel: ADMIN_SAMPLE_SOURCE,
      detail: 'Illustrative example. ' + (metric.detail || ''),
    })),
    commandModules: (baseConfig.commandModules || []).map((module) => ({
      ...module,
      dataState: 'sample',
      sourceLabel: ADMIN_SAMPLE_SOURCE,
      summary: 'Illustrative example. ' + (module.summary || ''),
      lastUpdated: 'for demonstration only (not a live refresh)',
      kpis: (module.kpis || []).map((kpi) => ({ ...kpi })),
      details: [...(module.details || [])],
    })),
    decisionPanel: baseConfig.decisionPanel ? {
      ...baseConfig.decisionPanel,
      summary: 'Illustrative example, not live decisions. ' + (baseConfig.decisionPanel.summary || ''),
      actions: (baseConfig.decisionPanel.actions || []).map((action) => ({
        ...action,
        detail: 'Illustrative example. ' + (action.detail || ''),
      })),
    } : null,
    prioritiesTitle: 'Illustrative school priorities',
    priorities: (baseConfig.priorities || []).map((item) => ({
      ...item,
      detail: 'Illustrative example. ' + (item.detail || ''),
      state: 'Sample',
    })),
    alerts: (baseConfig.alerts || []).map((item) => ({
      ...item,
      detail: 'Illustrative example. ' + (item.detail || ''),
    })),
    trendPanels: (baseConfig.trendPanels || []).map((panel) => ({
      ...panel,
      chip: 'Illustrative trend — not live',
      trend: Array.isArray(panel.trend) ? panel.trend.map((point) => ({ ...point })) : panel.trend,
    })),
    activityTitle: 'Illustrative activity feed',
    activities: (baseConfig.activities || []).map((item) => 'Example: ' + item),
    statuses: (baseConfig.statuses || []).map((status) => ({
      ...status,
      state: 'Example: ' + status.state,
    })),
    operationsTitle: 'Illustrative department readiness',
    operations: (baseConfig.operations || []).map((operation) => ({
      ...operation,
      updated: 'Sample (not synced)',
    })),
    rightRailSections: (baseConfig.rightRailSections || []).map((section) => ({
      ...section,
      title: 'Sample: ' + section.title,
      detail: section.detail ? 'Illustrative example. ' + section.detail : section.detail,
      items: Array.isArray(section.items) ? [...section.items] : section.items,
    })),
  };
}

export default function SchoolAdministratorDashboard() {
  const baseConfig = useMemo(() => getDashboardTemplate('schoolAdministrator'), []);
  const [snapshot, setSnapshot] = useState({
    serviceState: 'checking',
    successfulEndpointCount: 0,
  });

  useEffect(() => {
    let active = true;

    loadSchoolAdministratorLiveSnapshot()
      .then((nextSnapshot) => {
        if (active) {
          setSnapshot(nextSnapshot);
        }
      })
      .catch(() => {
        if (active) {
          setSnapshot({ serviceState: 'unavailable', successfulEndpointCount: 0 });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const config = useMemo(
    () => buildAdministratorDemoConfig(baseConfig, snapshot),
    [baseConfig, snapshot],
  );

  return (
    <>
      <CrownDashboardTemplate config={config} roleKey="schoolAdministrator" />
      <SandboxAdminTransactionPanel />
      <details><summary>Open school classroom operations and records</summary>
        <ClassroomOperations audience="admin" /><ClassroomWorkspace audience="admin" /><ClassroomLeadership audience="admin" />
      </details>
    </>
  );
}
