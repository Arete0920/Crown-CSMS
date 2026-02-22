import React from "react";

/**
 * CrownLayout – app shell with sidebar + main content area.
 *
 * Props:
 *   title    – page heading (h2)
 *   subtitle – secondary line under heading (muted)
 *   right    – JSX slotted to the top-right of the page header
 *   children – page body
 */
export default function CrownLayout({ title, subtitle, right, children, mainClassName = "" }) {
  return (
    <div className="crown-app">
      <aside className="crown-sidebar">
        <h1>Crown</h1>
        <div className="crown-badge">Demo / Internal</div>
        <div
          style={{
            marginTop: 16,
            opacity: 0.9,
            fontSize: 12,
            lineHeight: 1.5,
          }}
        >
          Strong. Secure. School-ready.
        </div>
      </aside>

      <main className={`crown-main ${mainClassName}`.trim()}>
        {(title || subtitle || right) && (
          <div className="crown-pagehead">
            <div>
              {title && <h2 className="crown-title">{title}</h2>}
              {subtitle && <p className="crown-subtitle">{subtitle}</p>}
            </div>
            {right && <div>{right}</div>}
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
