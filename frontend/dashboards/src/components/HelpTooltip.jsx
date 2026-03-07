/**
 * HelpTooltip.jsx
 *
 * Contextual inline help icon. On click, fetches and renders a help article.
 *
 * Props:
 *   slug   (string) — HelpArticle slug
 *   label  (string) — accessible label for the button (default: "Help")
 */
import { useState } from "react";
import { apiFetch } from "../utils/apiFetch";

export function HelpTooltip({ slug, label = "Help" }) {
  const [article, setArticle] = useState(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  function toggle() {
    if (open) {
      setOpen(false);
      return;
    }
    if (article) {
      setOpen(true);
      return;
    }
    setLoading(true);
    apiFetch(`/api/v1/help/${slug}/`)
      .then((res) => res.json())
      .then((data) => {
        setArticle(data);
        setOpen(true);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }

  return (
    <span className="help-tooltip-wrapper" style={{ position: "relative", display: "inline-block" }}>
      <button
        type="button"
        onClick={toggle}
        aria-label={label}
        aria-expanded={open}
        aria-controls={`help-${slug}`}
        className="help-tooltip-btn"
        style={{
          background: "none",
          border: "1px solid #999",
          borderRadius: "50%",
          width: 18,
          height: 18,
          cursor: "pointer",
          fontSize: 11,
          lineHeight: "16px",
          padding: 0,
        }}
      >
        ?
      </button>
      {open && article && (
        <div
          id={`help-${slug}`}
          role="tooltip"
          aria-label={article.title}
          style={{
            position: "absolute",
            zIndex: 999,
            background: "#fff",
            border: "1px solid #ddd",
            borderRadius: 4,
            padding: "10px 14px",
            minWidth: 220,
            maxWidth: 360,
            boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
            top: 22,
            left: 0,
          }}
        >
          <strong>{article.title}</strong>
          <p style={{ marginTop: 6, fontSize: 13 }}>{article.content}</p>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close help"
            style={{ marginTop: 6, fontSize: 12, cursor: "pointer" }}
          >
            Close
          </button>
        </div>
      )}
      {loading && <span aria-live="polite" style={{ fontSize: 11 }}>…</span>}
    </span>
  );
}
