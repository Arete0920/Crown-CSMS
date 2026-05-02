import CrownCard from '../launch/CrownCard.jsx';
import CrownDashboardShell from './CrownDashboardShell.jsx';
import CrownDashboardHeader from './CrownDashboardHeader.jsx';
import CrownDashboardMetricGrid from './CrownDashboardMetricGrid.jsx';
import CrownDashboardMetricCard from './CrownDashboardMetricCard.jsx';
import CrownInsightPanel from './CrownInsightPanel.jsx';
import CrownQuickActions from './CrownQuickActions.jsx';
import CrownDashboardActivityFeed from './CrownDashboardActivityFeed.jsx';
import CrownDashboardStatusPanel from './CrownDashboardStatusPanel.jsx';
import CrownModuleSection from './CrownModuleSection.jsx';
import CrownDashboardEmptyState from './CrownDashboardEmptyState.jsx';
import CrownDashboardErrorState from './CrownDashboardErrorState.jsx';
import CrownDashboardFlipCard from './CrownDashboardFlipCard.jsx';
import CrownDashboardRightRail from './CrownDashboardRightRail.jsx';
import CrownFaithCommunityStrip from './CrownFaithCommunityStrip.jsx';
import { Link, useInRouterContext } from 'react-router-dom';
import { BASE_FAITH_COMMUNITY } from '../../config/dashboardTemplates/_baseData.js';

function renderActionsByRole(actions = [], roleKey) {
  return actions.filter((action) => {
    if (!action.allowedRoles?.length) return true;
    return action.allowedRoles.includes(roleKey);
  });
}

export default function CrownDashboardTemplate({ config, roleKey }) {
  const hasRouterContext = useInRouterContext();

  if (!config || typeof config !== 'object') {
    return <CrownDashboardErrorState title="Dashboard unavailable" message="Dashboard configuration is missing or invalid." />;
  }

  const actions = renderActionsByRole(config.quickActions || [], roleKey);
  const metrics = Array.isArray(config.metrics) ? config.metrics : [];
  const statuses = Array.isArray(config.statuses) ? config.statuses : [];
  const activities = Array.isArray(config.activities) ? config.activities : [];
  const operations = Array.isArray(config.operations) ? config.operations : [];
  const insight = config.insight || {};
  const trendPanels = Array.isArray(config.trendPanels) ? config.trendPanels : [];
  const priorities = Array.isArray(config.priorities) ? config.priorities : [];
  const alerts = Array.isArray(config.alerts) ? config.alerts : [];
  const commandModules = Array.isArray(config.commandModules) ? config.commandModules : [];
  const rightRailSections = Array.isArray(config.rightRailSections) ? config.rightRailSections : [];

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
    >
      <CrownDashboardHeader
        eyebrow={config.eyebrow}
        title={config.title}
        subtitle={config.subtitle}
      />

      <CrownFaithCommunityStrip faithCommunity={config.faithCommunity ?? BASE_FAITH_COMMUNITY} />

      <div className="launch-content">
        {isRichLayout ? (
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

            {operations.length > 0 ? (
              <CrownCard>
                <div className="launch-card-heading-row">
                  <div>
                    <div className="launch-section-kicker">Department readiness</div>
                    <h3>{config.operationsTitle}</h3>
                  </div>
                </div>
                <div className="launch-table-wrap">
                  <table className="launch-table">
                    <thead>
                      <tr>
                        <th>Department</th>
                        <th>Owner</th>
                        <th>Readiness</th>
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
            ) : null}

            <section className="launch-dashboard-grid launch-dashboard-grid-secondary">
              <CrownQuickActions actions={actions} />
              <CrownDashboardStatusPanel
                kicker={config.statusKicker || 'Operational status'}
                title={config.statusTitle}
                statuses={statuses}
              />

            </section>
          </>
        ) : (
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
          </>
        )}

        {config.errorState ? (
          <CrownDashboardErrorState title={config.errorState.title} message={config.errorState.message} />
        ) : null}

        {operations.length && !isSchoolAdminCommandCenter ? (
          <CrownCard>
            <div className="launch-card-heading-row">
              <div>
                <div className="launch-section-kicker">Operational Detail</div>
                <h3>{config.operationsTitle}</h3>
              </div>
              {hasRouterContext ? (
                <Link to={config.exportSummaryHref || '/integrity'} className="launch-button launch-button-secondary">Export Summary</Link>
              ) : (
                <a href={config.exportSummaryHref || '/integrity'} className="launch-button launch-button-secondary">Export Summary</a>
              )}
            </div>
            <div className="launch-table-wrap">
              <table className="launch-table">
                <thead>
                  <tr>
                    <th>Area</th>
                    <th>Owner</th>
                    <th>Status</th>
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
        ) : null}
      </div>
    </CrownDashboardShell>
  );
}
