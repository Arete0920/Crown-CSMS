import CrownCard from '../launch/CrownCard.jsx';

function getTruthLabel(dataState) {
  const state = String(dataState || '').toLowerCase();
  if (state === 'live') return 'Live';
  if (state === 'fallback') return 'Fallback';
  if (state === 'sample') return 'Sample';
  if (state === 'loading') return 'Loading';
  if (state === 'unavailable') return 'Unavailable';
  if (state === 'none') return 'None';
  return '';
}

function getTruthClass(dataState) {
  const state = String(dataState || '').toLowerCase();
  if (state === 'live') return 'is-good';
  if (state === 'loading') return 'is-info';
  return 'is-warn';
}

export default function CrownDashboardMetricCard({ label, value, detail, accent = 'blue', dataState, sourceLabel }) {
  const badge = String(label || '').trim().slice(0, 1).toUpperCase();
  const truthLabel = getTruthLabel(dataState);
  const truthClass = getTruthClass(dataState);
  const truthTitle = sourceLabel ? `${truthLabel} · ${sourceLabel}` : truthLabel;

  return (
    <CrownCard className={`launch-metric-card launch-accent-${accent}`}>
      <div className="launch-metric-toprow">
        <div className="launch-metric-label">{label}</div>
        <div className="launch-metric-meta">
          {truthLabel ? (
            <span className={`launch-data-truth-pill ${truthClass}`} title={truthTitle}>
              {truthLabel}
            </span>
          ) : null}
          <div className="launch-metric-icon-bubble" aria-hidden="true">{badge || 'C'}</div>
        </div>
      </div>
      <div className="launch-metric-value">{value}</div>
      <div className="launch-metric-detail">{detail}</div>
    </CrownCard>
  );
}
