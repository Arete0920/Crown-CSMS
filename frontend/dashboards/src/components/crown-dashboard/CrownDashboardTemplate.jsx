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

function renderActionsByRole(actions = [], roleKey) {
  return actions.filter((action) => {
    if (!action.allowedRoles?.length) return true;
    return action.allowedRoles.includes(roleKey);
  });
}

export default function CrownDashboardTemplate({ config, roleKey }) {
  const actions = renderActionsByRole(config.quickActions, roleKey);

  return (
    <CrownDashboardShell activePath={config.activePath} schoolName={config.schoolName}>
      <CrownDashboardHeader
        eyebrow={config.eyebrow}
        title={config.title}
        subtitle={config.subtitle}
        note={config.note}
      />

      <div className="launch-content">
        <CrownDashboardMetricGrid>
          {config.metrics.map((card) => (
            <CrownDashboardMetricCard key={card.label} {...card} />
          ))}
        </CrownDashboardMetricGrid>

        <section className="launch-dashboard-grid launch-dashboard-grid-primary">
          <CrownInsightPanel
            kicker={config.insight.kicker}
            title={config.insight.title}
            chip={config.insight.chip}
            trend={config.insight.trend}
          />
          <CrownDashboardActivityFeed title={config.activityTitle} items={config.activities} />
        </section>

        <section className="launch-dashboard-grid launch-dashboard-grid-secondary">
          <CrownQuickActions actions={actions} />
          <CrownDashboardStatusPanel title={config.statusTitle} statuses={config.statuses} />
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
              title="Live records are not required for visual review"
              message="Sandbox preview data shown. Connect backend for live records."
            />
          </section>
        ) : null}

        {config.errorState ? (
          <CrownDashboardErrorState title={config.errorState.title} message={config.errorState.message} />
        ) : null}

        {config.operations?.length ? (
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
                  {config.operations.map((row) => (
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
