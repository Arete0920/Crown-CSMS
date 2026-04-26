import CrownCard from './CrownCard.jsx';

export default function CrownEmptyState({ title, message }) {
  return (
    <CrownCard className="launch-state-card">
      <div className="launch-state-icon" aria-hidden="true">&nbsp;</div>
      <h3>{title}</h3>
      <p>{message}</p>
    </CrownCard>
  );
}