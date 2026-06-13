import PropTypes from 'prop-types';

function getTruthLabel(dataState) {
  const state = String(dataState || '').toLowerCase();
  if (state === 'live') return 'Live';
  if (state === 'fallback') return 'Fallback';
  if (state === 'sample') return 'Sample';
  if (state === 'loading') return 'Loading';
  if (state === 'unavailable') return 'Unavailable';
  if (state === 'none') return 'None';
  return 'Fallback';
}

function getTruthClass(dataState) {
  const state = String(dataState || '').toLowerCase();
  if (state === 'live') return 'is-good';
  if (state === 'loading') return 'is-info';
  return 'is-warn';
}

export default function CrownDashboardDataTruthStatus({ dataState, sourceLabel, lastSyncLabel }) {
  const truthLabel = getTruthLabel(dataState);
  const truthClass = getTruthClass(dataState);

  return (
    <section className='launch-data-truth-status' aria-label='Data truth status'>
      <div className='launch-data-truth-status-copy'>
        <div className='launch-section-kicker'>Data truth</div>
        <h3>Source and sync status</h3>
        <p>{sourceLabel}</p>
      </div>
      <div className='launch-data-truth-status-meta'>
        <span className={`launch-data-truth-pill ${truthClass}`}>{truthLabel}</span>
        <span className='launch-data-truth-sync'>{lastSyncLabel}</span>
      </div>
    </section>
  );
}

CrownDashboardDataTruthStatus.propTypes = {
  dataState: PropTypes.string,
  sourceLabel: PropTypes.string,
  lastSyncLabel: PropTypes.string,
};
