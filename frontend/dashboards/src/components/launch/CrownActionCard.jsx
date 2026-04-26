import CrownCard from './CrownCard.jsx';

export default function CrownActionCard({ title, description, actionLabel, eyebrow = 'Quick Action' }) {
  return (
    <CrownCard className="launch-action-card">
      <div className="launch-action-eyebrow">{eyebrow}</div>
      <h3>{title}</h3>
      <p>{description}</p>
      <button type="button" className="launch-button launch-button-secondary">{actionLabel}</button>
    </CrownCard>
  );
}
