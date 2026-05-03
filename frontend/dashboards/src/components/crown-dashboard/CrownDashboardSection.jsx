import CrownCard from '../launch/CrownCard.jsx';
import { Link, useInRouterContext } from 'react-router-dom';

export default function CrownDashboardSection({ kicker = 'Overview', title, body, actions = [] }) {
  const hasRouterContext = useInRouterContext();

  return (
    <CrownCard>
      <div className="launch-section-kicker">{kicker}</div>
      <h3>{title}</h3>
      {body ? <p className="launch-body-copy">{body}</p> : null}
      {actions.length ? (
        <div className="launch-inline-actions">
          {actions.map((action) => (
            (action.href || action.fallbackHref || '/dashboard') ? (
              hasRouterContext ? (
                <Link
                  key={action.label}
                  to={action.href || action.fallbackHref || '/dashboard'}
                  className={`launch-button ${action.tone === 'secondary' ? 'launch-button-secondary' : 'launch-button-primary'}`}
                >
                  {action.label}
                </Link>
              ) : (
                <a
                  key={action.label}
                  href={action.href || action.fallbackHref || '/dashboard'}
                  className={`launch-button ${action.tone === 'secondary' ? 'launch-button-secondary' : 'launch-button-primary'}`}
                >
                  {action.label}
                </a>
              )
            ) : null
          ))}
        </div>
      ) : null}
    </CrownCard>
  );
}
