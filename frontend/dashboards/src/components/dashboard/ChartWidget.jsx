/**
 * ChartWidget — sparkline/donut stub for Phase A.
 * Phase B: replace with recharts or similar.
 */
import React from "react";

// Simple inline donut using SVG — no external chart library needed for Phase A.
function DonutChart({ segments }) {
  if (!segments?.length) return <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>No data</div>;

  const COLOR_MAP = { good: "var(--crown-ok)", warn: "var(--crown-warn)", bad: "var(--crown-danger)" };
  const total = segments.reduce((s, seg) => s + (seg.value ?? 0), 0) || 1;

  let angle = -90; // start at top
  const cx = 60, cy = 60, r = 42, stroke = 16;

  const arcs = segments.map((seg) => {
    const pct = seg.value / total;
    const sweep = pct * 360;
    const startAngle = angle;
    angle += sweep;
    const endAngle = angle;

    const toRad = (d) => (d * Math.PI) / 180;
    const x1 = cx + r * Math.cos(toRad(startAngle));
    const y1 = cy + r * Math.sin(toRad(startAngle));
    const x2 = cx + r * Math.cos(toRad(endAngle));
    const y2 = cy + r * Math.sin(toRad(endAngle));
    const large = sweep > 180 ? 1 : 0;

    return {
      d: `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`,
      color: COLOR_MAP[seg.color] ?? "var(--crown-muted)",
      label: seg.label,
      value: seg.value,
      pct: Math.round(pct * 100),
    };
  });

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
      <svg width={120} height={120} viewBox="0 0 120 120" aria-label="Donut chart">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--crown-border)" strokeWidth={stroke} />
        {arcs.map((arc, i) => (
          <path
            key={i}
            d={arc.d}
            fill="none"
            stroke={arc.color}
            strokeWidth={stroke}
            strokeLinecap="round"
          />
        ))}
        <text x={cx} y={cy + 5} textAnchor="middle" fontSize={11} fill="var(--crown-muted)">{total}</text>
      </svg>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {arcs.map((arc, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
            <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: arc.color, flexShrink: 0 }} />
            <span style={{ color: "var(--crown-muted)" }}>{arc.label}</span>
            <span style={{ fontWeight: 700, color: arc.color }}>{arc.value}</span>
            <span style={{ color: "var(--crown-muted)", fontSize: 11 }}>({arc.pct}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Simple sparkline using SVG path.
function SparkLine({ series }) {
  if (!series?.length) return <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>No data</div>;
  const COLORS = ["var(--crown-gold)", "var(--crown-ok)", "var(--crown-info)"];

  return (
    <div>
      <svg width="100%" height={80} viewBox="0 0 280 80" preserveAspectRatio="none" aria-label="Trend chart">
        {series.map((s, si) => {
          const pts = s.points ?? [];
          if (!pts.length) return null;
          const ys = pts.map(p => p.y);
          const minY = Math.min(...ys), maxY = Math.max(...ys);
          const rangeY = maxY - minY || 1;
          const w = 280, h = 80;
          const coords = pts.map((p, i) => {
            const x = (i / (pts.length - 1)) * w;
            const y = h - ((p.y - minY) / rangeY) * (h - 10) - 5;
            return `${x},${y}`;
          });
          return (
            <polyline
              key={si}
              points={coords.join(" ")}
              fill="none"
              stroke={COLORS[si % COLORS.length]}
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          );
        })}
      </svg>
      <div style={{ display: "flex", gap: 12, marginTop: 4, flexWrap: "wrap" }}>
        {series.map((s, si) => (
          <div key={si} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12 }}>
            <span style={{ display: "inline-block", width: 20, height: 2, background: COLORS[si % COLORS.length], borderRadius: 2 }} />
            <span style={{ color: "var(--crown-muted)" }}>{s.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ChartWidget({ widget, onExpand }) {
  const { title, subtitle, data, type } = widget;

  return (
    <div className="crown-card" style={{ height: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <div>
          <div style={{ fontWeight: 800 }}>{title}</div>
          {subtitle && <div style={{ fontSize: 12, color: "var(--crown-muted)", marginTop: 2 }}>{subtitle}</div>}
        </div>
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

      {type === "chart_donut"
        ? <DonutChart segments={data?.segments} />
        : <SparkLine series={data?.series} />
      }
    </div>
  );
}
