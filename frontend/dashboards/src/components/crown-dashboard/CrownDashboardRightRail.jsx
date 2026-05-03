import CrownCard from '../launch/CrownCard.jsx';

function renderItems(items = []) {
  return (
    <ul className="launch-rail-list">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function renderMetricCard(section) {
  return (
    <CrownCard key={section.title} className={`launch-rail-card launch-rail-card-metric launch-rail-accent-${section.accent || 'blue'}`}>
      <div className="launch-section-kicker">{section.kicker}</div>
      <h3>{section.title}</h3>
      <div className="launch-rail-metric-display">
        <div className="launch-rail-metric-value">{section.metric}</div>
        {section.detail && <div className="launch-rail-metric-detail">{section.detail}</div>}
      </div>
      {section.items && section.items.length > 0 ? (
        <div className="launch-rail-items-preview">
          {renderItems(section.items.slice(0, 2))}
        </div>
      ) : null}
    </CrownCard>
  );
}

function renderGaugeCard(section) {
  const percentage = section.total ? Math.round((section.metric / section.total) * 100) : 0;
  return (
    <CrownCard key={section.title} className={`launch-rail-card launch-rail-card-gauge launch-rail-accent-${section.accent || 'gold'}`}>
      <div className="launch-section-kicker">{section.kicker}</div>
      <h3>{section.title}</h3>
      <div className="launch-rail-gauge">
        <div className="launch-rail-gauge-arc">
          <div className="launch-rail-gauge-progress" style={{ width: `${percentage}%` }}></div>
        </div>
        <div className="launch-rail-gauge-text">
          <span className="launch-rail-gauge-value">{section.metric}/{section.total}</span>
          <span className="launch-rail-gauge-pct">{percentage}%</span>
        </div>
      </div>
      {section.detail && <div className="launch-rail-gauge-detail">{section.detail}</div>}
    </CrownCard>
  );
}

function renderActivityCard(section) {
  return (
    <CrownCard key={section.title} className={`launch-rail-card launch-rail-card-activity launch-rail-accent-${section.accent || 'emerald'}`}>
      <div className="launch-section-kicker">{section.kicker}</div>
      <h3>{section.title}</h3>
      <div className="launch-rail-activity-badge">{section.metric}</div>
      {section.items && section.items.length > 0 ? (
        <ul className="launch-rail-list launch-rail-list-activity">
          {section.items.slice(0, 3).map((item) => (
            <li key={item} className="launch-rail-activity-item">
              <span className="launch-rail-activity-dot"></span>
              {item}
            </li>
          ))}
        </ul>
      ) : null}
    </CrownCard>
  );
}

function renderStatusCard(section) {
  return (
    <CrownCard key={section.title} className={`launch-rail-card launch-rail-card-status`}>
      <div className="launch-section-kicker">{section.kicker}</div>
      <h3>{section.title}</h3>
      <div className="launch-rail-status-items">
        {section.statuses && section.statuses.length > 0 ? (
          section.statuses.map((status) => (
            <div key={status.label} className={`launch-rail-status-row is-${status.state}`}>
              <span className="launch-rail-status-indicator"></span>
              <span className="launch-rail-status-label">{status.label}</span>
            </div>
          ))
        ) : null}
      </div>
      {section.items && section.items.length > 0 ? (
        <ul className="launch-rail-list launch-rail-list-compact">
          {section.items.slice(0, 2).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </CrownCard>
  );
}

function renderAlertCard(section) {
  return (
    <CrownCard key={section.title} className={`launch-rail-card launch-rail-card-alert launch-rail-accent-${section.accent || 'warn'}`}>
      <div className="launch-section-kicker">{section.kicker}</div>
      <h3>{section.title}</h3>
      <div className="launch-rail-alert-badge">{section.metric}</div>
      {section.detail && <div className="launch-rail-alert-detail">{section.detail}</div>}
      {section.items && section.items.length > 0 ? (
        <ul className="launch-rail-list launch-rail-list-alert">
          {section.items.slice(0, 2).map((item) => (
            <li key={item} className="launch-rail-alert-item">
              ⚠ {item}
            </li>
          ))}
        </ul>
      ) : null}
    </CrownCard>
  );
}

export default function CrownDashboardRightRail({ sections = [] }) {
  const renderCard = (section) => {
    const cardType = section.type || 'default';

    switch (cardType) {
      case 'metric':
        return renderMetricCard(section);
      case 'gauge':
        return renderGaugeCard(section);
      case 'activity':
        return renderActivityCard(section);
      case 'status':
        return renderStatusCard(section);
      case 'alert':
        return renderAlertCard(section);
      default:
        return (
          <CrownCard key={section.title} className="launch-rail-card">
            <div className="launch-section-kicker">{section.kicker || 'Context'}</div>
            <h3>{section.title}</h3>
            {renderItems(section.items)}
          </CrownCard>
        );
    }
  };

  return (
    <div className="launch-right-rail-content" aria-label="Context rail">
      {sections.map((section) => renderCard(section))}
    </div>
  );
}
