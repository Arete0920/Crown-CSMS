
export default function ErrorBanner({ title = "Something went wrong", message, correlationId }) {
  if (!message) return null;

  return (
    <div
      className="crown-alert crown-alert-danger"
      role="alert"
      style={{
        marginBottom: 12,
        background: "var(--crown-compat-color-f19de237c6)",
        border: "1px solid var(--crown-compat-color-3871da3420)",
        color: "var(--crown-compat-color-5e76dc6d1c)",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 6 }}>{title}</div>
      <div style={{ whiteSpace: "pre-wrap" }}>{message}</div>
      {correlationId ? (
        <div style={{ marginTop: 8, fontFamily: "var(--crown-font-mono)", opacity: 0.9 }}>
          correlation_id: {correlationId}
        </div>
      ) : null}
    </div>
  );
}
