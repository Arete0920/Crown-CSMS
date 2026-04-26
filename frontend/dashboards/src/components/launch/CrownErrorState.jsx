import CrownCard from './CrownCard.jsx';

export default function CrownErrorState({ title, message }) {
  return (
    <CrownCard className="launch-state-card launch-state-card-warn">
      <div className="launch-state-icon launch-state-icon-warn" aria-hidden="true">&nbsp;</div>
      <h3>{title}</h3>
      <p>{message}</p>
    </CrownCard>
  );
}