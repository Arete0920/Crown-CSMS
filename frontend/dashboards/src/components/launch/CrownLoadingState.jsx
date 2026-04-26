import CrownCard from './CrownCard.jsx';

export default function CrownLoadingState({ title = 'Preparing launch preview' }) {
  return (
    <CrownCard className="launch-state-card">
      <div className="launch-loading-bar" />
      <h3>{title}</h3>
      <p>Assembling the CROWN launch workspace.</p>
    </CrownCard>
  );
}