import { Link, useInRouterContext } from 'react-router-dom';
import { useState } from 'react';
import CrownCard from '../launch/CrownCard.jsx';

function ActionControl({ href, className, children, onClick, type = 'button' }) {
  const hasRouterContext = useInRouterContext();

  if (href) {
    return hasRouterContext ? (
      <Link to={href} className={className}>{children}</Link>
    ) : (
      <a href={href} className={className}>{children}</a>
    );
  }

  return (
    <button type={type} className={className} onClick={onClick}>
      {children}
    </button>
  );
}

export default function CrownDashboardFlipCard({ module }) {
  const [flipped, setFlipped] = useState(false);

  return (
    <CrownCard className={`launch-flip-card ${flipped ? 'is-flipped' : ''}`}>
      {!flipped ? (
        <div className="launch-flip-face launch-flip-face-front">
          <div className="launch-flip-head">
            <span className="launch-module-icon" aria-hidden="true">{module.icon || 'OP'}</span>
            <span className={`launch-status-pill ${module.statusTone === 'warn' ? 'is-warn' : 'is-good'}`}>
              {module.status}
            </span>
          </div>
          <div className="launch-section-kicker">{module.title}</div>
          <h3>{module.mainKpi}</h3>
          <p>{module.summary}</p>
          <ul className="launch-module-kpi-list">
            {(module.kpis || []).map((kpi) => (
              <li key={`${module.key}-${kpi.label}`}>
                <span>{kpi.label}</span>
                <strong>{kpi.value}</strong>
              </li>
            ))}
          </ul>
          <div className="launch-inline-actions">
            <ActionControl href={module.primaryActionHref} className="launch-button launch-button-primary">
              {module.primaryActionLabel}
            </ActionControl>
            <ActionControl className="launch-button launch-button-secondary" onClick={() => setFlipped(true)}>
              View Detail
            </ActionControl>
          </div>
        </div>
      ) : (
        <div className="launch-flip-face launch-flip-face-back">
          <div className="launch-flip-head">
            <span className="launch-section-kicker">{module.title} details</span>
            <button type="button" className="launch-button launch-button-secondary" onClick={() => setFlipped(false)}>
              Back
            </button>
          </div>
          <ul className="launch-flip-detail-list">
            {(module.details || []).map((detail) => (
              <li key={`${module.key}-${detail}`}>{detail}</li>
            ))}
          </ul>
          <div className="launch-flip-footer">
            <ActionControl href={module.backActionHref || module.primaryActionHref} className="launch-button launch-button-primary">
              {module.backActionLabel || module.primaryActionLabel}
            </ActionControl>
            <span>Updated {module.lastUpdated}</span>
          </div>
        </div>
      )}
    </CrownCard>
  );
}
