import { Link, useInRouterContext } from 'react-router';
import CrownCard from '../launch/CrownCard.jsx';

function ActionLink({ href, children }) {
  const hasRouterContext = useInRouterContext();

  if (!href) {
    return <span>{children}</span>;
  }

  if (hasRouterContext) {
    return <Link to={href}>{children}</Link>;
  }

  return <a href={href}>{children}</a>;
}

export default function CrownDashboardDecisionPanel({ panel }) {
  if (!panel || !Array.isArray(panel.actions) || panel.actions.length === 0) {
    return null;
  }

  return (
    <CrownCard className="launch-decision-panel">
      <div className="launch-decision-panel-header">
        <div>
          <div className="launch-section-kicker">{panel.kicker || 'Today\'s decisions'}</div>
          <h3>{panel.title || 'What needs action now'}</h3>
          {panel.summary ? <p>{panel.summary}</p> : null}
        </div>

        {panel.primaryMetric ? (
          <div className="launch-decision-panel-metric" aria-label={panel.primaryMetricLabel || 'Primary decision metric'}>
            <strong>{panel.primaryMetric}</strong>
            <span>{panel.primaryMetricLabel || 'items'}</span>
          </div>
        ) : null}
      </div>

      <div className="launch-decision-panel-grid">
        {panel.actions.map((item) => (
          <ActionLink key={`${item.label}-${item.value}`} href={item.href}>
            <article className={`launch-decision-item ${item.tone === 'warn' ? 'is-warn' : 'is-good'}`}>
              <span className="launch-decision-item-value">{item.value}</span>
              <span className="launch-decision-item-label">{item.label}</span>
              <small>{item.detail}</small>
            </article>
          </ActionLink>
        ))}
      </div>
    </CrownCard>
  );
}
