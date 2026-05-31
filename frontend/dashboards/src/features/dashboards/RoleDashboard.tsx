import { useEffect, useMemo, useState } from "react";
import type { DashboardApiPayload, DashboardRoleKey } from "./dashboardTypes";
import { getDashboardProfile, requiredSharedDashboardCards } from "./roleDashboardMatrix";
import { loadRoleDashboardPayload } from "./dashboardApi";
import { SharedDashboardWidgets } from "./shared/SharedDashboardWidgets";
import LearningContinuityPanel from "./LearningContinuityPanel";
import "./crown-dashboard.css";

interface RoleDashboardProps {
  readonly roleKey: DashboardRoleKey;
}

function urgencyLabel(urgency: string) {
  switch (urgency) {
    case "critical":
      return "Critical";
    case "high":
      return "High";
    case "medium":
      return "Medium";
    default:
      return "Normal";
  }
}

export function RoleDashboard({ roleKey }: Readonly<RoleDashboardProps>) {
  const profile = useMemo(() => getDashboardProfile(roleKey), [roleKey]);
  const [payload, setPayload] = useState<DashboardApiPayload | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    loadRoleDashboardPayload(roleKey).then((data) => {
      if (!active) return;
      setPayload(data);
      setLoaded(true);
    });
    return () => {
      active = false;
    };
  }, [roleKey]);

  const kpis = payload?.kpis?.length ? payload.kpis : profile.kpis;
  const queue = payload?.queue?.length ? payload.queue : profile.queue;
  const panels = payload?.panels?.length ? payload.panels : profile.panels;
  const dataMode = payload?.mode ?? "fallback";

  return (
    <main className={`crown-dashboard crown-dashboard-${profile.tone}`} data-testid={`dashboard-${profile.key}`}>
      <header className="crown-dashboard-hero">
        <div>
          <p className="crown-eyebrow">CROWN role dashboard</p>
          <h1>{profile.title}</h1>
          <p className="crown-dashboard-purpose">{profile.purpose}</p>
          <div className="crown-dashboard-audience">{profile.audience}</div>
        </div>
        <div className="crown-dashboard-status-card">
          <span className="crown-status-label">Data mode</span>
          <strong>{loaded ? dataMode : "loading"}</strong>
          <small>
            Live API data is used when available. Safe configured values render when live dashboard API is not yet connected.
          </small>
        </div>
      </header>

      <section className="crown-dashboard-section" aria-label="Role responsibilities">
        <div className="crown-section-heading">
          <div>
            <p className="crown-eyebrow">Role-specific responsibilities</p>
            <h2>What this dashboard is responsible for</h2>
          </div>
        </div>
        <div className="crown-responsibility-grid">
          {profile.primaryResponsibilities.map((item) => (
            <div className="crown-responsibility-card" key={item}>
              {item}
            </div>
          ))}
        </div>
      </section>

      <section className="crown-kpi-grid" aria-label="Role KPIs">
        {kpis.map((kpi) => (
          <article className={`crown-kpi-card crown-tone-${kpi.tone ?? profile.tone}`} key={kpi.label}>
            <span>{kpi.label}</span>
            <strong>{kpi.value}</strong>
            <p>{kpi.helper}</p>
            <small>Source: {kpi.source}</small>
          </article>
        ))}
      </section>

      <section className="crown-dashboard-split">
        <div className="crown-dashboard-section">
          <div className="crown-section-heading">
            <div>
              <p className="crown-eyebrow">Action queue</p>
              <h2>What needs attention</h2>
            </div>
          </div>
          <div className="crown-queue-list">
            {queue.map((item) => (
              <a className="crown-queue-item" href={item.href} key={item.title}>
                <span>
                  <strong>{item.title}</strong>
                  <small>{urgencyLabel(item.urgency)} priority</small>
                </span>
                <b>{item.count}</b>
              </a>
            ))}
          </div>
        </div>

        <div className="crown-dashboard-section">
          <div className="crown-section-heading">
            <div>
              <p className="crown-eyebrow">Quick actions</p>
              <h2>Common work shortcuts</h2>
            </div>
          </div>
          <div className="crown-action-list">
            {profile.quickActions.map((action) => (
              <a className="crown-action-card" href={action.href} key={action.label}>
                <strong>{action.label}</strong>
                <small>{action.description}</small>
              </a>
            ))}
          </div>
        </div>
      </section>

      <section className="crown-panel-grid" aria-label="Role panels">
        {panels.map((panel) => (
          <article className="crown-detail-panel" key={panel.title}>
            <p className="crown-eyebrow">Role panel</p>
            <h2>{panel.title}</h2>
            <p>{panel.description}</p>
            <ul>
              {panel.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>

      <LearningContinuityPanel roleKey={profile.key} />

      <SharedDashboardWidgets />

      <section className="crown-dashboard-section" aria-label="Microsoft integration status">
        <div className="crown-section-heading">
          <div>
            <p className="crown-eyebrow">Microsoft school ecosystem</p>
            <h2>Microsoft 365, Microsoft Education, and Teams</h2>
          </div>
        </div>
        <div className="crown-ms-grid">
          <article>
            <strong>Microsoft 365</strong>
            <span>Outlook, OneDrive, SharePoint, identity, and documents.</span>
          </article>
          <article>
            <strong>Microsoft Education</strong>
            <span>Classroom, assignment, and education workflow readiness.</span>
          </article>
          <article>
            <strong>Teams</strong>
            <span>Class, staff, leadership, board, and role-based collaboration channels.</span>
          </article>
          <article>
            <strong>Shared cards verified</strong>
            <span>{requiredSharedDashboardCards.length} required shared tools on this dashboard.</span>
          </article>
        </div>
      </section>
    </main>
  );
}
