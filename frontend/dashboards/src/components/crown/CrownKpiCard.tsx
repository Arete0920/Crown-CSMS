import React from "react";

type CrownKpiCardProps = {
  label: string;
  value: string | number;
  context?: string;
  status?: "pass" | "review" | "fail";
};

export function CrownKpiCard({
  label,
  value,
  context,
  status = "review",
}: CrownKpiCardProps) {
  const statusLabel =
    status === "pass" ? "On Track" : status === "fail" ? "Needs Action" : "Review";

  return (
    <section className="crown-card crown-kpi">
      <div className="flex items-start justify-between gap-3">
        <div className="crown-kpi-label">{label}</div>
        <span className={`crown-status crown-status-${status}`}>{statusLabel}</span>
      </div>
      <div className="crown-kpi-value">{value}</div>
      {context ? <div className="crown-kpi-context">{context}</div> : null}
    </section>
  );
}
