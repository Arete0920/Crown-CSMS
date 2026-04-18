
export default function EmptyState({ title = "Nothing to show yet", message, actionLabel, onAction }) {
  return (
    <div className="crown-card" style={{ padding: 14 }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>{title}</div>
      {message ? <div style={{ opacity: 0.9, marginBottom: 10 }}>{message}</div> : null}
      {actionLabel && onAction ? (
        <button className="crown-btn" type="button" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
