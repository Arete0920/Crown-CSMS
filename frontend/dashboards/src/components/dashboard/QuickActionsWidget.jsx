/**
 * QuickActionsWidget — grid of fast-jump action buttons.
 */

export default function QuickActionsWidget({ widget }) {
  const { title, data } = widget;
  const actions = data?.actions ?? [];

  return (
    <div className="crown-card" style={{ height: "100%" }}>
      <div style={{ fontWeight: 800, marginBottom: 12 }}>{title}</div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
          gap: 8,
        }}
      >
        {actions.map((action, i) => (
          <a
            key={i}
            href={action.to}
            className="crown-btn"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              fontWeight: 600,
              padding: "8px 14px",
              borderRadius: 10,
              background: "var(--crown-subtle)",
              border: "1px solid var(--crown-border)",
              color: "var(--crown-text)",
              textDecoration: "none",
              transition: "background 0.15s, border-color 0.15s",
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--crown-gold)"; e.currentTarget.style.color = "var(--crown-gold)"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--crown-border)"; e.currentTarget.style.color = "var(--crown-text)"; }}
          >
            <span style={{ flexShrink: 0 }}>→</span>
            {action.label}
          </a>
        ))}
      </div>
    </div>
  );
}
