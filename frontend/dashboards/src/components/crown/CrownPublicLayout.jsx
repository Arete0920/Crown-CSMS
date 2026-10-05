import { HelpTooltip } from '../HelpTooltip.jsx';
const BUILD_SHA = (import.meta?.env?.VITE_BUILD_SHA || "dev").slice(0, 7);
const DEPLOY_TAG = import.meta?.env?.VITE_DEPLOY_TAG || "";

export default function CrownPublicLayout({ title, subtitle, right, helpNotice, children }) {
  return (
    <div style={{ minHeight: "100vh", background: "var(--crown-bg)" }}>
      <header
        style={{
          borderBottom: "1px solid var(--crown-border)",
          background: "var(--crown-surface)",
        }}
      >
        <div
          style={{
            maxWidth: 980,
            margin: "0 auto",
            padding: "18px 20px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
          }}
        >
          <a
            href="/"
            style={{
              color: "var(--crown-text)",
              textDecoration: "none",
              fontWeight: 800,
              letterSpacing: 0.2,
            }}
          >
            Crown Admissions
          </a>
          {right ? <div>{right}</div> : null}
        </div>
      </header>

      <main style={{ padding: "26px 16px 34px" }}>
        <div style={{ maxWidth: 980, margin: "0 auto" }}>
          {(title || subtitle) && (
            <section style={{ marginBottom: 16 }}>
              {title ? <h1 className="crown-title">{title}</h1> : null}
              {subtitle ? <p className="crown-subtitle">{subtitle}</p> : null}
            </section>
          )}

          {helpNotice ? (
            <section
              className="crown-card"
              style={{ marginBottom: 14, padding: "10px 14px", fontSize: 13 }}
            >
              <HelpTooltip context={{ route_path: "/admissions", module: "admissions" }} />
              {helpNotice}
            </section>
          ) : null}

          {children}
        </div>
      </main>

      <footer
        style={{
          borderTop: "1px solid var(--crown-border)",
          color: "var(--crown-muted)",
          fontSize: 11,
          textAlign: "right",
          padding: "10px 16px 14px",
        }}
      >
        Build: {BUILD_SHA}{DEPLOY_TAG ? `  ${DEPLOY_TAG}` : ""}
      </footer>
    </div>
  );
}
