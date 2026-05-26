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
import { Link, useInRouterContext } from 'react-router-dom';
import { BASE_FAITH_COMMUNITY } from '../../config/dashboardTemplates/_baseData.js';

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

function buildDashboardModel(config, roleKey) {
  const defaultDataState = config.dataState || 'fallback';
  const defaultSourceLabel = config.sourceLabel || 'Dashboard template data';

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
  const { metrics, priorities, alerts, commandModules, trendPanels, activities, operations, actions, statuses } = model;

  return (
    <>
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

  if (!config || typeof config !== 'object') {
    return <CrownDashboardErrorState title="Dashboard unavailable" message="Dashboard configuration is missing or invalid." />;
  }

  const model = buildDashboardModel(config, roleKey);
  const { commandModules, rightRailSections } = model;

  // Admin command center: SchoolAdministrator gets admin metric grid + right rail.
  // Rich layout: any dashboard with commandModules gets priorities/alerts/flip-cards/trends.
  const isSchoolAdminCommandCenter = config.key === 'schoolAdministrator';
  const isRichLayout = isSchoolAdminCommandCenter || commandModules.length > 0;

  return (
    <CrownDashboardShell
      activePath={config.activePath}
      schoolName={config.schoolName}
      user={config.user}
      updatesCount={config.updatesCount}
      rightRail={(isSchoolAdminCommandCenter && rightRailSections.length > 0) ? <CrownDashboardRightRail sections={rightRailSections} /> : null}
      topbarSlot={
        <CrownHeroHeader
          schoolName={config.schoolName}
          userInitials={config.user?.initials}
          userAvatar={config.user?.avatar}
          updatesCount={config.updatesCount}
          title={config.title}
          heroMessage={config.heroMessage}
        />
      }
    >

      <CrownFaithCommunityStrip faithCommunity={config.faithCommunity ?? BASE_FAITH_COMMUNITY} />

      {config.note && (
        <div className="launch-sandbox-banner">{config.note}</div>
      )}

      <div className="launch-content">
        {config.dashboardTitle && (
          <h2 className="launch-dashboard-section-title">{config.dashboardTitle}</h2>
        )}
        {isRichLayout ? (
          renderRichLayout(config, model, hasRouterContext, isSchoolAdminCommandCenter)
        ) : (
          renderStandardLayout(config, model, hasRouterContext)
        )}

        {config.errorState ? (
          <CrownDashboardErrorState title={config.errorState.title} message={config.errorState.message} />
        ) : null}
      </div>
    </CrownDashboardShell>
  );
}
