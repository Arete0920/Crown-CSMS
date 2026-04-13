/**
 * DrilldownDrawer - slide-in panel that shows detail rows for a widget.
 * Uses the Crown CSS card + overlay pattern (no external drawer library).
 */
import PropTypes from "prop-types";
import { useEffect } from "react";

export default function DrilldownDrawer({ open, title, onClose, children }) {
  useEffect(() => {
    if (!open) return;
    const handler = (event) => {
      if (event.key === "Escape") onClose();
    };
    globalThis.addEventListener("keydown", handler);
    return () => globalThis.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <dialog
      open
      aria-modal="true"
      aria-label={`${title} detail`}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 999,
        display: "flex",
        justifyContent: "flex-end",
        border: 0,
        margin: 0,
        padding: 0,
        background: "transparent",
      }}
    >
      <button
        type="button"
        onClick={onClose}
        aria-label={`Close ${title} detail overlay`}
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(0,0,0,0.55)",
          border: 0,
          padding: 0,
          margin: 0,
          cursor: "pointer",
        }}
      />
      <div
        style={{
          position: "relative",
          width: "min(440px, 95vw)",
          height: "100%",
          background: "var(--crown-surface)",
          borderLeft: "1px solid var(--crown-border)",
          overflowY: "auto",
          padding: 24,
          boxShadow: "var(--crown-shadow)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <div style={{ fontWeight: 800, fontSize: 17 }}>{title}</div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close drawer"
            style={{
              background: "none",
              border: "1px solid var(--crown-border)",
              borderRadius: 8,
              cursor: "pointer",
              color: "var(--crown-muted)",
              padding: "4px 10px",
              fontSize: 16,
            }}
          >
            x
          </button>
        </div>

        {children ?? (
          <div style={{ color: "var(--crown-muted)", fontSize: 13, fontStyle: "italic" }}>
            Drilldown detail coming in Phase B.
          </div>
        )}
      </div>
    </dialog>
  );
}

DrilldownDrawer.propTypes = {
  open: PropTypes.bool.isRequired,
  title: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  children: PropTypes.node,
};
