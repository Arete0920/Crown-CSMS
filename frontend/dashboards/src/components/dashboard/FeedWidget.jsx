/**
 * FeedWidget — compact list of recent items (messages, events, alerts).
 */

export default function FeedWidget({ widget, onExpand }) {
  const { title, subtitle, data } = widget;
  const threads = data?.threads ?? data?.events ?? data?.items ?? [];

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

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {threads.length === 0 ? (
          <div style={{ fontSize: 13, color: "var(--crown-muted)", fontStyle: "italic" }}>No items</div>
        ) : (
          threads.map((item, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: 10,
                padding: "6px 0",
                borderBottom: i < threads.length - 1 ? "1px solid var(--crown-border)" : "none",
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {item.from ?? item.name ?? item.subject ?? item.text ?? ""}
                </div>
                {(item.subject ?? item.date) && (
                  <div style={{ fontSize: 12, color: "var(--crown-muted)", marginTop: 2 }}>
                    {item.subject ?? item.date}
                  </div>
                )}
              </div>
              {(item.ago ?? item.date) && (
                <div style={{ fontSize: 11, color: "var(--crown-muted)", flexShrink: 0, marginTop: 2 }}>
                  {item.ago ?? item.date}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
