import { Link, useInRouterContext } from 'react-router-dom';
import CrownCard from './CrownCard.jsx';

export default function CrownActionCard({ title, description, actionLabel, eyebrow = 'Quick Action', href }) {
  const hasRouterContext = useInRouterContext();

  return (
    <CrownCard className="launch-action-card">
      <div className="launch-action-eyebrow">{eyebrow}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      {href ? (
        hasRouterContext ? (
          <Link to={href} className="launch-button launch-button-secondary">{actionLabel}</Link>
        ) : (
          <a href={href} className="launch-button launch-button-secondary">{actionLabel}</a>
        )
      ) : (
        <button type="button" className="launch-button launch-button-secondary">{actionLabel}</button>
      )}
    </CrownCard>
  );
}
