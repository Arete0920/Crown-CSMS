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

function renderActionsByRole(actions = [], roleKey) {
  return actions.filter((action) => {
    if (!action.allowedRoles?.length) return true;
    return action.allowedRoles.includes(roleKey);
  });
}

export default function CrownDashboardTemplate({ config, roleKey }) {
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

  const isSchoolAdminCommandCenter = config.key === 'schoolAdministrator';
  const adminHeroMetrics = metrics.slice(0, 4);
  const adminSnapshot = [
    priorities[0] ? { label: 'Immediate decision', value: priorities[0].title } : null,
    alerts[0] ? { label: 'Highest alert', value: alerts[0].title } : null,
    operations[0] ? { label: 'First watch area', value: operations[0].area } : null,
  ].filter(Boolean);

  return (
    <CrownDashboardShell
      activePath={config.activePath}
      schoolName={config.schoolName}
      user={config.user}
      updatesCount={config.updatesCount}
      rightRail={isSchoolAdminCommandCenter ? <CrownDashboardRightRail sections={rightRailSections} /> : null}
    >
      <CrownDashboardHeader
        eyebrow={config.eyebrow}
        title={config.title}
        subtitle={config.subtitle}
        note={config.note}
      />

      <div className="launch-content">
        {isSchoolAdminCommandCenter ? (
          <>
            <section className="launch-admin-hero-grid">
              <CrownCard className="launch-admin-brief-card">
                <div className="launch-card-heading-row launch-card-heading-row-tight">
                  <div>
                    <div className="launch-section-kicker">Administrator brief</div>
                    <h3>Whole-school command posture</h3>
                  </div>
                  <span className="launch-chip">Morning view</span>
                </div>
                <p className="launch-admin-brief-copy">
                  Enrollment momentum is healthy, operations are stable overall, and the main leadership load is concentrated in admissions decisions, attendance recovery, and same-day exceptions.
                </p>
                <div className="launch-admin-snapshot-list">
                  {adminSnapshot.map((item) => (
                    <div key={item.label} className="launch-admin-snapshot-item">
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </div>
                  ))}
                </div>
              </CrownCard>

              <CrownCard className="launch-admin-hero-metrics-card">
                <div className="launch-card-heading-row launch-card-heading-row-tight">
                  <div>
                    <div className="launch-section-kicker">Executive metrics</div>
                    <h3>Leadership scorecard</h3>
                  </div>
                </div>
                <div className="launch-admin-hero-metrics-grid">
                  {adminHeroMetrics.map((card) => (
                    <div key={card.label} className={`launch-admin-hero-metric launch-accent-${card.accent || 'blue'}`}>
                      <span>{card.label}</span>
                      <strong>{card.value}</strong>
                    </div>
                  ))}
                </div>
              </CrownCard>
            </section>

            <section className="launch-admin-section-block">
              <div className="launch-admin-section-headline">
                <div>
                  <div className="launch-section-kicker">Executive overview</div>
                  <h3>Core performance indicators</h3>
                </div>
                <p>Dense operational signals for the school day, tuned for quick scanning.</p>
              </div>
            <CrownDashboardMetricGrid className="launch-dashboard-grid-metrics-admin">
              {metrics.map((card) => (
                <CrownDashboardMetricCard key={card.label} {...card} />
              ))}
            </CrownDashboardMetricGrid>
            </section>

            <section className="launch-dashboard-grid launch-dashboard-grid-primary">
              <CrownCard className="launch-priority-card">
                <div className="launch-section-kicker">Today's priorities</div>
                <h3>Leadership execution queue</h3>
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
            </section>

            <section className="launch-admin-section-block">
              <div className="launch-admin-section-headline">
                <div>
                  <div className="launch-section-kicker">Operational command grid</div>
                  <h3>Department control surfaces</h3>
                </div>
                <p>Each module highlights current pressure, readiness, and the next decisive action.</p>
              </div>
            <section className="launch-dashboard-grid launch-dashboard-grid-module launch-command-grid">
              {commandModules.map((module) => (
                <CrownDashboardFlipCard key={module.key} module={module} />
              ))}
            </section>
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

            <section className="launch-dashboard-grid launch-dashboard-grid-secondary">
              <CrownQuickActions actions={actions} />
              <CrownDashboardStatusPanel
                kicker={config.statusKicker || 'Operational status'}
                title={config.statusTitle}
                statuses={statuses}
              />
              <CrownDashboardEmptyState
                title="Sandbox preview"
                message="Sandbox preview data shown. Connect backend for live records."
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
                <CrownDashboardEmptyState
                  title="Sandbox preview"
                  message="Live records are not required for this visual review pass."
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
              <button type="button" className="launch-button launch-button-secondary">Export Summary</button>
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
