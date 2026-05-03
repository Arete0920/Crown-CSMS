import { requiredSharedDashboardCards } from "../roleDashboardMatrix";

export function SharedDashboardWidgets() {
  return (
    <section className="crown-dashboard-section" aria-label="Shared dashboard tools">
      <div className="crown-section-heading">
        <div>
          <p className="crown-eyebrow">Required on every dashboard</p>
          <h2>Communication, calendar, mission life, and Microsoft tools</h2>
        </div>
      </div>
      <div className="crown-shared-grid">
        {requiredSharedDashboardCards.map((card) => (
          <a className="crown-shared-card" href={card.href} key={card.key} data-testid={`shared-card-${card.key}`}>
            <span className="crown-shared-icon" aria-hidden="true">
              {card.title.slice(0, 1)}
            </span>
            <span>
              <strong>{card.title}</strong>
              <small>{card.description}</small>
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}