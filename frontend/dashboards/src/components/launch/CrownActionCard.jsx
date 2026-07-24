import { Link, useInRouterContext } from 'react-router';
import CrownCard from './CrownCard.jsx';

export default function CrownActionCard({ title, description, actionLabel, eyebrow = 'Quick Action', href, fallbackHref = '/dashboard' }) {
  const hasRouterContext = useInRouterContext();
  const targetHref = href || fallbackHref || '/dashboard';

  return (
    <CrownCard className="launch-action-card">
      <div className="launch-action-eyebrow">{eyebrow}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      {hasRouterContext ? (
        <Link to={targetHref} className="launch-button launch-button-secondary">{actionLabel}</Link>
      ) : (
        <a href={targetHref} className="launch-button launch-button-secondary">{actionLabel}</a>
      )}
    </CrownCard>
  );
}
