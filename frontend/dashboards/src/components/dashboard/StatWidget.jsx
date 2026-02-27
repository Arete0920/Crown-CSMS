/**
 * StatWidget — single KPI tile: large value + label + optional hint.
 * Extends CrownMetricCard with expand + status coloring.
 */
import React from "react";

const STATUS_COLOR = {
  good: "var(--crown-ok)",
  warn: "var(--crown-warn)",
  bad: "var(--crown-danger)",
  due_soon: "var(--crown-warn)",
};

export default function StatWidget({ widget, onExpand }) {
  const { title, subtitle, data } = widget;
  const rawVal = data?.count ?? data?.amount ?? data?.total ?? "--";
  const label  = data?.label ?? subtitle ?? "";
  const hint   = data?.currency ? `${data.currency}` : "";
  const status = data?.status;
  const valueColor = status ? STATUS_COLOR[status] ?? "inherit" : "inherit";

  const formatted =
    typeof rawVal === "number" && data?.currency
      ? new Intl.NumberFormat("en-US", { style: "currency", currency: data.currency }).format(rawVal)
      : typeof rawVal === "number"
      ? rawVal.toLocaleString()
      : rawVal;

  return (
    <div className="crown-card" style={{ height: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 700, color: "var(--crown-muted)", textTransform: "uppercase", letterSpacing: 0.5 }}>
          {title}
        </span>
        {onExpand && (
          <button
            onClick={onExpand}
            aria-label={`Expand ${title}`}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--crown-muted)", fontSize: 16, padding: 2 }}
          >
            ⤢
          </button>
        )}
      </div>

      <div style={{ fontSize: 28, fontWeight: 900, color: valueColor, lineHeight: 1.1 }}>
        {formatted}
      </div>

      {label && (
        <div style={{ fontSize: 12, color: "var(--crown-muted)", marginTop: 4 }}>
          {label}{hint ? ` · ${hint}` : ""}
        </div>
      )}
    </div>
  );
}
