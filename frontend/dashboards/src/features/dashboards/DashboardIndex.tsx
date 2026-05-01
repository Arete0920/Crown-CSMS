import { roleDashboardProfiles } from "./roleDashboardMatrix";
import "./crown-dashboard.css";

export function DashboardIndex() {
  return (
    <main className="crown-dashboard crown-dashboard-royal" data-testid="dashboard-index">
      <header className="crown-dashboard-hero">
        <div>
          <p className="crown-eyebrow">CROWN dashboard system</p>
          <h1>Role Dashboard Index</h1>
          <p className="crown-dashboard-purpose">
            Every dashboard uses one shared shell, one route registry, required shared communication/mission/Microsoft tools,
            and role-specific KPIs matched to actual responsibilities.
          </p>
        </div>
      </header>
      <section className="crown-role-index-grid">
        {roleDashboardProfiles.map((profile) => (
          <a href={profile.route} className="crown-role-index-card" key={profile.key}>
            <strong>{profile.title}</strong>
            <span>{profile.audience}</span>
            <small>{profile.purpose}</small>
          </a>
        ))}
      </section>
    </main>
  );
}