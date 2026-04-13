/**
 * FlipWidget - front shows summary, back shows next-step items.
 */
import { useState } from "react";

const LEVEL_COLOR = {
  good: "#86efac",
  warn: "#fde68a",
  bad: "#fca5a5",
  info: "#bfdbfe",
};

const LEVEL_LABEL = {
  good: "o",
  warn: "!",
  bad: "x",
};

export default function FlipWidget({ widget, onExpand }) {
  const [flipped, setFlipped] = useState(false);
  const { title, subtitle, data } = widget;
  const front = data?.front ?? { good: 0, warn: 0, bad: 0 };
  const backItems = data?.back?.items ?? [];

  const toggleFlipped = () => setFlipped((value) => !value);
  const handleKeyDown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleFlipped();
    }
  };

  return (
    <div
      style={{
        height: "100%",
        minHeight: 200,
        perspective: 900,
        cursor: "pointer",
        userSelect: "none",
      }}
      onClick={toggleFlipped}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-pressed={flipped}
      aria-label={`Flip ${title} widget`}
    >
      <div
        style={{
          position: "relative",
          height: "100%",
          minHeight: 200,
          transformStyle: "preserve-3d",
          transition: "transform 0.42s cubic-bezier(0.4,0.2,0.2,1)",
          transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
        }}
      >
        <div
          aria-hidden={flipped}
          style={{
            backfaceVisibility: "hidden",
            WebkitBackfaceVisibility: "hidden",
            position: "absolute",
            inset: 0,
            background: "var(--crown-brand)",
            borderRadius: 10,
            padding: "16px 18px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            boxShadow: "0 2px 8px rgba(15,23,42,0.18)",
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.65)", textTransform: "uppercase", letterSpacing: 0.9 }}>
                {title}
              </div>
              {subtitle && (
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.45)", marginTop: 2 }}>{subtitle}</div>
              )}
            </div>
            {onExpand && (
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  onExpand();
                }}
                aria-label={`Expand ${title}`}
                style={{ background: "none", border: "none", cursor: "pointer", color: "rgba(255,255,255,0.5)", fontSize: 16, padding: 2 }}
              >
                []
              </button>
            )}
          </div>

          <div style={{ display: "flex", gap: 18, justifyContent: "center", padding: "12px 0 8px" }}>
            <Metric label="Good" value={front.good} color={LEVEL_COLOR.good} />
            <Metric label="Watch" value={front.warn} color={LEVEL_COLOR.warn} />
            <Metric label="Action" value={front.bad} color={LEVEL_COLOR.bad} />
          </div>

          <div style={{ textAlign: "right", fontSize: 9, color: "rgba(255,255,255,0.35)", textTransform: "uppercase", letterSpacing: 0.6 }}>
            TAP FOR DETAILS
          </div>
        </div>

        <div
          aria-hidden={!flipped}
          style={{
            backfaceVisibility: "hidden",
            WebkitBackfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
            position: "absolute",
            inset: 0,
            background: "var(--crown-gold)",
            borderRadius: 10,
            padding: "16px 18px",
            display: "flex",
            flexDirection: "column",
            gap: 0,
            boxShadow: "0 2px 8px rgba(15,23,42,0.18)",
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.8)", textTransform: "uppercase", letterSpacing: 0.9, marginBottom: 10 }}>
            {title} - Action Items
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 7, flex: 1, overflow: "hidden" }}>
            {backItems.length === 0 ? (
              <div style={{ fontSize: 13, color: "rgba(255,255,255,0.7)", fontStyle: "italic" }}>No action items</div>
            ) : backItems.slice(0, 5).map((item, index) => (
              <div key={index} style={{ fontSize: 12, display: "flex", gap: 7, alignItems: "flex-start", color: "#fff" }}>
                <span style={{ color: LEVEL_COLOR[item.level] ?? "rgba(255,255,255,0.6)", flexShrink: 0, marginTop: 1, fontSize: 11 }}>
                  {LEVEL_LABEL[item.level] ?? "-"}
                </span>
                <span style={{ lineHeight: 1.4 }}>{item.text}</span>
              </div>
            ))}
          </div>
          <div style={{ textAlign: "right", fontSize: 9, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: 0.6, marginTop: 8 }}>
            TAP TO FLIP BACK
          </div>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, color }) {
  return (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{ fontSize: 28, fontWeight: 900, color, lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.55)", marginTop: 4, textTransform: "uppercase", letterSpacing: 0.6 }}>{label}</div>
    </div>
  );
}
