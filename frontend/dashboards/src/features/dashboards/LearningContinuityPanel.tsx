import React from "react";
import type { DashboardRoleKey } from "./dashboardTypes";
import { getLearningContinuityPayload, type LearningContinuitySection } from "./learningContinuityData";

interface LearningContinuityPanelProps {
  readonly roleKey: DashboardRoleKey;
}

function ToneBadge({ tone, children }: Readonly<{ tone: string; children: React.ReactNode }>) {
  return <span className={`continuity-tone continuity-tone-${tone}`}>{children}</span>;
}

function MetricCard({ label, value, helper, tone }: LearningContinuitySection["metrics"][number]) {
  return (
    <article className="continuity-metric-card">
      <header>
        <span className="continuity-metric-label">{label}</span>
        <ToneBadge tone={tone}>{value}</ToneBadge>
      </header>
      <p>{helper}</p>
    </article>
  );
}

function ActionCard({ label, href, helper, tone }: LearningContinuitySection["actions"][number]) {
  return (
    <a className="continuity-action-card" href={href}>
      <div>
        <h5>{label}</h5>
        <p>{helper}</p>
      </div>
      <ToneBadge tone={tone}>Open</ToneBadge>
    </a>
  );
}

function SectionPanel({ section }: Readonly<{ section: LearningContinuitySection }>) {
  return (
    <section className="continuity-section-panel" aria-label={section.title}>
      <div className="continuity-section-header">
        <p className="continuity-kicker">{section.kicker}</p>
        <h4>{section.title}</h4>
        <p>{section.description}</p>
      </div>

      <div className="continuity-metric-grid">
        {section.metrics.map((metric) => (
          <MetricCard key={`${section.title}-${metric.label}`} {...metric} />
        ))}
      </div>

      <div className="continuity-action-grid">
        {section.actions.map((action) => (
          <ActionCard key={`${section.title}-${action.label}`} {...action} />
        ))}
      </div>
    </section>
  );
}

export default function LearningContinuityPanel({ roleKey }: Readonly<LearningContinuityPanelProps>) {
  const payload = React.useMemo(() => getLearningContinuityPayload(roleKey), [roleKey]);

  return (
    <section className="crown-card crown-learning-continuity" aria-label="Learning Continuity">
      <header className="continuity-hero">
        <p className="continuity-label">{payload.modeBanner.label}</p>
        <div className="continuity-hero-main">
          <div>
            <h3>{payload.modeBanner.title}</h3>
            <p>{payload.modeBanner.description}</p>
          </div>
          <div className="continuity-status">
            <span>Status</span>
            <strong>{payload.modeBanner.status}</strong>
            <p>{payload.modeBanner.helper}</p>
          </div>
        </div>
      </header>

      <div className="continuity-section-stack">
        {payload.sections.map((section) => (
          <SectionPanel key={section.title} section={section} />
        ))}
      </div>
    </section>
  );
}
