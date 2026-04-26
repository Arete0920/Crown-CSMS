import CrownCard from '../launch/CrownCard.jsx';

export default function CrownDashboardSection({ kicker = 'Overview', title, body, actions = [] }) {
  return (
    <CrownCard>
      <div className="launch-section-kicker">{kicker}</div>
      <h3>{title}</h3>
      {body ? <p className="launch-body-copy">{body}</p> : null}
      {actions.length ? (
        <div className="launch-inline-actions">
          {actions.map((action) => (
            action.href ? (
              <a
                key={action.label}
                href={action.href}
                className={`launch-button ${action.tone === 'secondary' ? 'launch-button-secondary' : 'launch-button-primary'}`}
              >
                {action.label}
              </a>
            ) : (
              <button
                key={action.label}
                type="button"
                className={`launch-button ${action.tone === 'secondary' ? 'launch-button-secondary' : 'launch-button-primary'}`}
              >
                {action.label}
              </button>
            )
          ))}
        </div>
      ) : null}
    </CrownCard>
  );
}
