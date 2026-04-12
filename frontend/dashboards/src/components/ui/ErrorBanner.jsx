
export default function ErrorBanner({ title = "Something went wrong", message, correlationId }) {
  if (!message) return null;

  return (
    <div className="crown-alert crown-alert-danger" role="alert" style={{ marginBottom: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>{title}</div>
      <div style={{ whiteSpace: "pre-wrap" }}>{message}</div>
      {correlationId ? (
        <div style={{ marginTop: 8, fontFamily: "monospace", opacity: 0.9 }}>
          correlation_id: {correlationId}
        </div>
      ) : null}
    </div>
  );
}
