import CrownCard from '../launch/CrownCard.jsx';
import CrownDashboardShell from './CrownDashboardShell.jsx';
import CrownHeroHeader from './CrownHeroHeader.jsx';
import CrownDashboardMetricGrid from './CrownDashboardMetricGrid.jsx';
import CrownDashboardMetricCard from './CrownDashboardMetricCard.jsx';
import CrownInsightPanel from './CrownInsightPanel.jsx';
import CrownQuickActions from './CrownQuickActions.jsx';
import CrownDashboardActivityFeed from './CrownDashboardActivityFeed.jsx';
import CrownDashboardStatusPanel from './CrownDashboardStatusPanel.jsx';
import CrownModuleSection from './CrownModuleSection.jsx';
import CrownDashboardErrorState from './CrownDashboardErrorState.jsx';
import CrownDashboardFlipCard from './CrownDashboardFlipCard.jsx';
import CrownDashboardRightRail from './CrownDashboardRightRail.jsx';
import CrownFaithCommunityStrip from './CrownFaithCommunityStrip.jsx';
import CrownDashboardCommunicationsStrip from './CrownDashboardCommunicationsStrip.jsx';
import CrownDashboardDataTruthStatus from './CrownDashboardDataTruthStatus.jsx';
import CrownDashboardDecisionPanel from './CrownDashboardDecisionPanel.jsx';
import { Link, useInRouterContext } from 'react-router-dom';
import { useMemo } from 'react';
import { BASE_COMMUNICATIONS, BASE_FAITH_COMMUNITY, BASE_NOTE } from '../../config/dashboardTemplates/_baseData.js';
import useDashboardData from '../../hooks/useDashboardData.js';

function getDefaultLastSyncLabel(dataState) {
  const state = String(dataState || '').toLowerCase();
  if (state === 'live') return 'Last synced just now';
  if (state === 'loading') return 'Sync in progress';
  if (state === 'unavailable') return 'Last sync unavailable';
  return 'Using configured fallback data';
}

function renderActionsByRole(actions, roleKey) {
  const safeActions = Array.isArray(actions) ? actions : [];
  return safeActions.filter((action) => {
    if (!action.allowedRoles?.length) return true;
    return action.allowedRoles.includes(roleKey);
  });
}

function applyDataTruth(items, dataState, sourceLabel) {
  const safeItems = Array.isArray(items) ? items : [];
  return safeItems.map((item) => ({
    ...item,
    dataState: item.dataState || dataState,
    sourceLabel: item.sourceLabel || sourceLabel,
  }));
}

function getAlertTone(level) {
  const normalized = String(level || '').toLowerCase();
  if (normalized === 'critical' || normalized === 'severe' || normalized === 'urgent') return 'bad';
  if (normalized === 'high' || normalized === 'medium') return 'warn';
  if (normalized === 'low' || normalized === 'info' || normalized === 'good') return 'good';
  return 'warn';
}

function getDashboardDataState(source, payload, error, loading) {
  const servedFrom = String(payload?.meta?.served_from || '').toLowerCase();

  if (loading) return 'loading';
  if (servedFrom === 'sample') return 'sample';
  if (source === 'live') return 'live';
  if (source === 'fallback') return 'fallback';
  if (source === 'none' && error) return 'error';
  if (source === 'none') return 'unavailable';
  return source || 'unavailable';
}

function getDashboardSourceLabel(dataState, endpoint, payload) {
  const servedFrom = String(payload?.meta?.served_from || '').toLowerCase();
  const snapshotSource = payload?.meta?.snapshot_source;

  if (servedFrom === 'snapshot') {
    return snapshotSource
      ? `Dashboard snapshot service (${snapshotSource})`
      : 'Dashboard snapshot service';
  }

  if (servedFrom === 'sample') {
    return `Dashboard summary service sample (${endpoint})`;
  }

  if (dataState === 'live') {
    return `Dashboard summary service (${endpoint})`;
  }

  if (dataState === 'loading') {
    return `Loading dashboard summary service (${endpoint})`;
  }

  if (dataState === 'fallback') {
    return `Frontend fallback dashboard data (${endpoint})`;
  }

  if (dataState === 'error' || dataState === 'unavailable') {
    return `Dashboard summary service unavailable (${endpoint})`;
  }

  return 'Static dashboard scaffold';
}

function getDashboardNote(dataState, sourceLabel) {
  if (dataState === 'live') {
    return `Live dashboard records active. ${sourceLabel}.`;
  }

  if (dataState === 'sample') {
    return `Sample dashboard records are explicitly labeled. ${sourceLabel}.`;
  }

  if (dataState === 'loading') {
    return `Loading dashboard records. ${sourceLabel}.`;
  }

  if (dataState === 'error' || dataState === 'unavailable') {
    return `Dashboard records are currently unavailable. ${sourceLabel}.`;
  }

  if (dataState === 'fallback') {
    return `Fallback dashboard records are explicitly labeled. ${sourceLabel}.`;
  }

  return sourceLabel;
}

function buildPriorityItems(queue, dataState, sourceLabel) {
  return (Array.isArray(queue) ? queue : []).map((item) => ({
    title: item,
    detail: sourceLabel,
    state: dataState === 'live' ? 'Live' : dataState === 'sample' ? 'Sample' : dataState === 'loading' ? 'Loading' : 'Attention',
    tone: dataState === 'live' ? 'good' : 'warn',
  }));
}

function buildAlertItems(alerts, sourceLabel) {
  return (Array.isArray(alerts) ? alerts : []).map((item) => ({
    title: item.title,
    detail: item.secondary || sourceLabel,
    tone: getAlertTone(item.level),
  }));
}

function buildLiveDashboardConfig(config, payload, endpointConfig, loading, error, source) {
  if (!config?.liveDataKey || config.disableLiveData) {
    return config;
  }

  const dataState = getDashboardDataState(source, payload, error, loading);
  const sourceLabel = getDashboardSourceLabel(dataState, endpointConfig?.endpoint, payload);
  const fallbackMetrics = Array.isArray(config.metrics) ? config.metrics : [];
  const payloadMetrics = Array.isArray(payload?.metrics) ? payload.metrics : [];
  const metrics = (payloadMetrics.length > 0 ? payloadMetrics : fallbackMetrics).map((item, index) => ({
    label: item.label,
    value: item.value,
    detail: item.secondary || fallbackMetrics[index]?.detail || sourceLabel,
    accent: fallbackMetrics[index]?.accent || item.accent || 'blue',
    dataState,
    sourceLabel,
  }));

  return {
    ...config,
    note: getDashboardNote(dataState, sourceLabel),
    metrics,
    priorities: buildPriorityItems(payload?.queue, dataState, sourceLabel),
    alerts: buildAlertItems(payload?.alerts, sourceLabel),
    statuses: [
      { label: 'Dashboard Data State', state: dataState },
      { label: 'Dashboard Data Source', state: sourceLabel },
      ...(Array.isArray(config.statuses) ? config.statuses : []),
    ],
    commandModules: applyDataTruth(config.commandModules, 'sample', 'Static dashboard scaffold'),
    errorState: (dataState === 'error' || dataState === 'unavailable') && metrics.length === 0
      ? {
          title: 'Dashboard data unavailable',
          message: sourceLabel,
        }
      : config.errorState,
  };
}

function buildDashboardModel(config, roleKey) {
  const defaultDataState = config.dataState || 'fallback';
  const defaultSourceLabel = config.sourceLabel || 'Static dashboard scaffold';

  return {
    actions: renderActionsByRole(config.quickActions, roleKey),
    metrics: applyDataTruth(config.metrics, defaultDataState, defaultSourceLabel),
    statuses: Array.isArray(config.statuses) ? config.statuses : [],
    activities: Array.isArray(config.activities) ? config.activities : [],
    operations: Array.isArray(config.operations) ? config.operations : [],
    insight: config.insight || {},
    trendPanels: Array.isArray(config.trendPanels) ? config.trendPanels : [],
    priorities: Array.isArray(config.priorities) ? config.priorities : [],
    alerts: Array.isArray(config.alerts) ? config.alerts : [],
    commandModules: applyDataTruth(config.commandModules, defaultDataState, defaultSourceLabel),
    decisionPanel: config.decisionPanel || null,
    rightRailSections: Array.isArray(config.rightRailSections) ? config.rightRailSections : [],
  };
}

function renderOperationsTable(config, operations, hasRouterContext, isSchoolAdminCommandCenter) {
  if (!operations.length) {
    return null;
  }

  const link = hasRouterContext ? (
    <Link to={config.exportSummaryHref || '/integrity'} className="launch-button launch-button-secondary">Export Summary</Link>
  ) : (
    <a href={config.exportSummaryHref || '/integrity'} className="launch-button launch-button-secondary">Export Summary</a>
  );

  return (
    <CrownCard>
      <div className="launch-card-heading-row">
        <div>
          <div className="launch-section-kicker">{isSchoolAdminCommandCenter ? 'Department readiness' : 'Operational Detail'}</div>
          <h3>{config.operationsTitle}</h3>
        </div>
        {isSchoolAdminCommandCenter ? null : link}
      </div>
      <div className="launch-table-wrap">
        <table className="launch-table">
          <thead>
            <tr>
              <th>{isSchoolAdminCommandCenter ? 'Department' : 'Area'}</th>
              <th>Owner</th>
              <th>{isSchoolAdminCommandCenter ? 'Readiness' : 'Status'}</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {operations.map((row) => (
              <tr key={`${row.area}-${row.owner}`}>
                <td>{row.area}</td>
                <td>{row.owner}</td>
                <td>{row.status}</td>
                <td>{row.updated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </CrownCard>
  );
}

function renderRichLayout(config, model, hasRouterContext, isSchoolAdminCommandCenter) {
  const { metrics, priorities, alerts, commandModules, trendPanels, activities, operations, actions, statuses, decisionPanel } = model;

  return (
    <>
      <CrownDashboardDecisionPanel panel={decisionPanel} />

      <CrownDashboardMetricGrid className={isSchoolAdminCommandCenter ? 'launch-dashboard-grid-metrics-admin' : undefined}>
        {metrics.map((card) => (
          <CrownDashboardMetricCard key={card.label} {...card} />
        ))}
      </CrownDashboardMetricGrid>

      {(priorities.length > 0 || alerts.length > 0) ? (
        <section className="launch-dashboard-grid launch-dashboard-grid-primary">
          {priorities.length > 0 ? (
            <CrownCard className="launch-priority-card">
              <div className="launch-section-kicker">Today's priorities</div>
              <h3>{config.prioritiesTitle || 'Execution queue'}</h3>
              <ul className="launch-priority-list">
                {priorities.map((item) => (
                  <li key={item.title}>
                    <div>
                      <strong>{item.title}</strong>
                      <span>{item.detail}</span>
                    </div>
                    <span className={`launch-status-pill ${item.tone === 'warn' ? 'is-warn' : 'is-good'}`}>{item.state}</span>
                  </li>
                ))}
              </ul>
            </CrownCard>
          ) : null}

          {alerts.length > 0 ? (
            <CrownCard className="launch-alert-card">
              <div className="launch-section-kicker">Alerts and exceptions</div>
              <h3>Action required</h3>
              <ul className="launch-alert-list">
                {alerts.map((item) => (
                  <li key={item.title} className={item.tone === 'warn' ? 'is-warn' : 'is-good'}>
                    <strong>{item.title}</strong>
                    <span>{item.detail}</span>
                  </li>
                ))}
              </ul>
            </CrownCard>
          ) : null}
        </section>
      ) : null}

      <section className="launch-dashboard-grid launch-dashboard-grid-module launch-command-grid">
        {commandModules.map((module) => (
          <CrownDashboardFlipCard key={module.key} module={module} />
        ))}
      </section>

      <section className="launch-dashboard-grid launch-dashboard-grid-analytics">
        {trendPanels.map((panel) => (
          <CrownInsightPanel
            key={panel.title}
            kicker={panel.kicker}
            title={panel.title}
            chip={panel.chip}
            trend={panel.trend}
          />
        ))}
        <CrownDashboardActivityFeed
          title={config.activityTitle}
          kicker={config.activityKicker || 'Recent activity'}
          items={activities}
        />
      </section>

      {renderOperationsTable(config, operations, hasRouterContext, isSchoolAdminCommandCenter)}

      <section className="launch-dashboard-grid launch-dashboard-grid-secondary">
        <CrownQuickActions actions={actions} />
        <CrownDashboardStatusPanel
          kicker={config.statusKicker || 'Operational status'}
          title={config.statusTitle}
          statuses={statuses}
        />
      </section>
    </>
  );
}

function renderStandardLayout(config, model, hasRouterContext) {
  const { metrics, insight, activities, actions, statuses, operations } = model;

  return (
    <>
      <CrownDashboardMetricGrid>
        {metrics.map((card) => (
          <CrownDashboardMetricCard key={card.label} {...card} />
        ))}
      </CrownDashboardMetricGrid>

      <section className="launch-dashboard-grid launch-dashboard-grid-primary">
        <CrownInsightPanel
          kicker={insight.kicker}
          title={insight.title}
          chip={insight.chip}
          trend={insight.trend}
        />
        <CrownDashboardActivityFeed
          title={config.activityTitle}
          kicker={config.activityKicker}
          items={activities}
        />
      </section>

      <section className="launch-dashboard-grid launch-dashboard-grid-secondary">
        <CrownQuickActions actions={actions} />
        <CrownDashboardStatusPanel
          kicker={config.statusKicker || 'System Status'}
          title={config.statusTitle}
          statuses={statuses}
        />
      </section>

      {config.moduleSection ? (
        <section className="launch-dashboard-grid launch-dashboard-grid-primary">
          <CrownModuleSection
            kicker={config.moduleSection.kicker}
            title={config.moduleSection.title}
            body={config.moduleSection.body}
            actions={config.moduleSection.actions || []}
          />
        </section>
      ) : null}

      {renderOperationsTable(config, operations, hasRouterContext, false)}
    </>
  );
}

export default function CrownDashboardTemplate({ config, roleKey }) {
  const hasRouterContext = useInRouterContext();

  const safeConfig = config && typeof config === 'object' ? config : null;
  const shouldLoadDashboardData = Boolean(safeConfig?.liveDataKey && !safeConfig?.disableLiveData);
  const dashboardData = useDashboardData(safeConfig?.liveDataKey || '', { enabled: shouldLoadDashboardData });
  const effectiveConfig = useMemo(
    () => buildLiveDashboardConfig(
      safeConfig,
      dashboardData.data,
      dashboardData.config,
      dashboardData.loading,
      dashboardData.error,
      dashboardData.source,
    ),
    [dashboardData.config, dashboardData.data, dashboardData.error, dashboardData.loading, dashboardData.source, safeConfig],
  );

  if (!safeConfig) {
    return <CrownDashboardErrorState title="Dashboard unavailable" message="Dashboard configuration is missing or invalid." />;
  }

  const model = buildDashboardModel(effectiveConfig, roleKey);
  const { commandModules, rightRailSections } = model;
  const dataState = effectiveConfig.dataState || 'fallback';
  const sourceLabel = effectiveConfig.sourceLabel || 'Static dashboard scaffold';
  const lastSyncLabel = effectiveConfig.lastSyncLabel || getDefaultLastSyncLabel(dataState);
  const communications = effectiveConfig.communications ?? BASE_COMMUNICATIONS;
  const isGenericBaseNote = effectiveConfig.note === BASE_NOTE;

  // Admin command center: SchoolAdministrator gets admin metric grid + right rail.
  // Rich layout: any dashboard with commandModules gets priorities/alerts/flip-cards/trends.
  const isSchoolAdminCommandCenter = effectiveConfig.key === 'schoolAdministrator';
  const isRichLayout = isSchoolAdminCommandCenter || commandModules.length > 0;

  return (
    <CrownDashboardShell
      activePath={effectiveConfig.activePath}
      schoolName={effectiveConfig.schoolName}
      user={effectiveConfig.user}
      updatesCount={effectiveConfig.updatesCount}
      rightRail={(isSchoolAdminCommandCenter && rightRailSections.length > 0) ? <CrownDashboardRightRail sections={rightRailSections} /> : null}
      topbarSlot={
        <CrownHeroHeader
          schoolName={effectiveConfig.schoolName}
          userInitials={effectiveConfig.user?.initials}
          userAvatar={effectiveConfig.user?.avatar}
          updatesCount={effectiveConfig.updatesCount}
          title={effectiveConfig.title}
          heroMessage={effectiveConfig.heroMessage}
        />
      }
    >

      <CrownFaithCommunityStrip faithCommunity={effectiveConfig.faithCommunity ?? BASE_FAITH_COMMUNITY} />

      <CrownDashboardCommunicationsStrip communications={communications} />

      <CrownDashboardDataTruthStatus
        dataState={dataState}
        sourceLabel={sourceLabel}
        lastSyncLabel={lastSyncLabel}
      />

      {effectiveConfig.note && !isGenericBaseNote && (
        <div className="launch-sandbox-banner">{effectiveConfig.note}</div>
      )}

      <div className="launch-content">
        {effectiveConfig.dashboardTitle && (
          <h2 className="launch-dashboard-section-title">{effectiveConfig.dashboardTitle}</h2>
        )}
        {isRichLayout ? (
          renderRichLayout(effectiveConfig, model, hasRouterContext, isSchoolAdminCommandCenter)
        ) : (
          renderStandardLayout(effectiveConfig, model, hasRouterContext)
        )}

        {effectiveConfig.errorState ? (
          <CrownDashboardErrorState title={effectiveConfig.errorState.title} message={effectiveConfig.errorState.message} />
        ) : null}
      </div>
    </CrownDashboardShell>
  );
}
