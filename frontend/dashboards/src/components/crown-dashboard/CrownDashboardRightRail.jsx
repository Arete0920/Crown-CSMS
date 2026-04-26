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

export default function CrownDashboardRightRail({ sections = [] }) {
  return (
    <div className="launch-right-rail-content" aria-label="Context rail">
      {sections.map((section) => (
        <CrownCard key={section.title} className="launch-rail-card">
          <div className="launch-section-kicker">{section.kicker || 'Context'}</div>
          <h3>{section.title}</h3>
          {section.quote ? <p className="launch-rail-quote">{section.quote}</p> : null}
          {renderItems(section.items)}
        </CrownCard>
      ))}
    </div>
  );
}
