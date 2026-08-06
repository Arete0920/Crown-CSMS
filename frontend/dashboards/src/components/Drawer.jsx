import PropTypes from "prop-types";
import { useEffect } from "react";

export default function Drawer({
  open,
  onClose,
  title,
  children,
  width = 420,
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    globalThis.addEventListener("keydown", onKey);
    return () => globalThis.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <button
        type="button"
        onClick={onClose}
        aria-label="Close drawer overlay"
        style={{
          position: "fixed",
          inset: 0,
          background: "var(--crown-compat-color-5338a3860b)",
          zIndex: 1000,
          border: 0,
          padding: 0,
          margin: 0,
          cursor: "pointer",
        }}
      />

      <dialog
        open
        aria-modal="true"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          height: "100vh",
          width,
          background: "var(--crown-surface)",
          zIndex: 1001,
          boxShadow: "-8px 0 24px var(--crown-compat-color-59b051b478)",
          display: "flex",
          flexDirection: "column",
          border: 0,
          margin: 0,
          padding: 0,
        }}
      >
        <div
          style={{
            padding: "14px 16px",
            borderBottom: "1px solid var(--crown-border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 8,
          }}
        >
          <div style={{ fontWeight: 600, fontSize: 16 }}>{title}</div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            style={{
              fontSize: 18,
              lineHeight: 1,
              padding: "2px 6px",
            }}
          >
            x
          </button>
        </div>

        <div style={{ padding: 16, overflowY: "auto", flex: 1 }}>
          {children}
        </div>
      </dialog>
    </>
  );
}

Drawer.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func,
  title: PropTypes.node,
  children: PropTypes.node,
  width: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};
