/**
 * DrilldownDrawer — slide-in panel that shows detail rows for a widget.
 * Uses the Crown CSS card + overlay pattern (no external drawer library).
 */
import React, { useEffect, useRef } from "react";

export default function DrilldownDrawer({ open, title, widget, schoolId, onClose, children }) {
  const overlayRef = useRef(null);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // Close on overlay click
  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose();
  };

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.55)",
        zIndex: 999,
        display: "flex",
        justifyContent: "flex-end",
      }}
      role="dialog"
      aria-modal="true"
      aria-label={`${title} detail`}
    >
      <div
        style={{
          width: "min(440px, 95vw)",
          height: "100%",
          background: "var(--crown-surface)",
          borderLeft: "1px solid var(--crown-border)",
          overflowY: "auto",
          padding: 24,
          boxShadow: "var(--crown-shadow)",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <div style={{ fontWeight: 800, fontSize: 17 }}>{title}</div>
          <button
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
            ✕
          </button>
        </div>

        {/* Body */}
        {children ?? (
          <div style={{ color: "var(--crown-muted)", fontSize: 13, fontStyle: "italic" }}>
            Drilldown detail coming in Phase B.
          </div>
        )}
      </div>
    </div>
  );
}
