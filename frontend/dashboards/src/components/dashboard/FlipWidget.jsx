/**
 * FlipWidget — front shows count summary, back shows next-step items.
 * CSS-only flip (no framer-motion dependency needed).
 */
import React, { useState } from "react";

const LEVEL_COLOR = {
  good: "var(--crown-ok)",
  warn: "var(--crown-warn)",
  bad:  "var(--crown-danger)",
  info: "var(--crown-info, #5aa9e6)",
};

const LEVEL_LABEL = {
  good: "●",
  warn: "◆",
  bad:  "▲",
};

export default function FlipWidget({ widget, onExpand }) {
  const [flipped, setFlipped] = useState(false);
  const { title, subtitle, data } = widget;
  const front = data?.front ?? { good: 0, warn: 0, bad: 0 };
  const backItems = data?.back?.items ?? [];

  return (
    <div className="crown-card" style={{ height: "100%", minHeight: 180, perspective: 1000 }}>
      {/* Card header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <div>
          <span style={{ fontSize: 13, fontWeight: 700, color: "var(--crown-muted)", textTransform: "uppercase", letterSpacing: 0.5 }}>
            {title}
          </span>
          {subtitle && (
            <div style={{ fontSize: 11, color: "var(--crown-muted)", marginTop: 2 }}>{subtitle}</div>
          )}
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

      {/* Flip container */}
      <div
        style={{
          position: "relative",
          minHeight: 110,
          transformStyle: "preserve-3d",
          transition: "transform 0.45s ease",
          transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
        }}
      >
        {/* Front face */}
        <div
          style={{ backfaceVisibility: "hidden", position: "absolute", inset: 0 }}
          aria-hidden={flipped}
        >
          <div style={{ display: "flex", gap: 20, marginBottom: 8 }}>
            <Metric label="Good" value={front.good} color={LEVEL_COLOR.good} />
            <Metric label="Watch" value={front.warn} color={LEVEL_COLOR.warn} />
            <Metric label="Action" value={front.bad} color={LEVEL_COLOR.bad} />
          </div>
        </div>

        {/* Back face */}
        <div
          style={{
            backfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            gap: 6,
          }}
          aria-hidden={!flipped}
        >
          <div style={{ fontSize: 11, color: "var(--crown-muted)", marginBottom: 2 }}>Next steps</div>
          {backItems.slice(0, 4).map((item, i) => (
            <div key={i} style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "flex-start" }}>
              <span style={{ color: LEVEL_COLOR[item.level] ?? "inherit", flexShrink: 0, marginTop: 1 }}>
                {LEVEL_LABEL[item.level] ?? "•"}
              </span>
              <span>{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Flip control */}
      <div style={{ marginTop: 14, display: "flex", justifyContent: "flex-end" }}>
        <button
          onClick={() => setFlipped(v => !v)}
          aria-label={flipped ? "Show summary" : "Show next steps"}
          className="crown-btn-sm"
          style={{
            background: "none",
            border: "1px solid var(--crown-border)",
            borderRadius: 8,
            color: "var(--crown-gold)",
            cursor: "pointer",
            fontSize: 12,
            fontWeight: 700,
            padding: "4px 12px",
          }}
        >
          {flipped ? "← Summary" : "Details →"}
        </button>
      </div>
    </div>
  );
}

function Metric({ label, value, color }) {
  return (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 24, fontWeight: 900, color }}>{value}</div>
      <div style={{ fontSize: 11, color: "var(--crown-muted)", marginTop: 2 }}>{label}</div>
    </div>
  );
}
