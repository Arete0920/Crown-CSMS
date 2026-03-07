import React, { useEffect, useState } from "react";

/**
 * CrownLayout – app shell with permission-derived sidebar + main content area.
 *
 * Props:
 *   title    – page heading (h2)
 *   subtitle – secondary line under heading (muted)
 *   right    – JSX slotted to the top-right of the page header
 *   children – page body
 */

function getSchoolId() {
  try {
    return sessionStorage.getItem("crown.school.id") || "";
  } catch { return ""; }
}

function getToken() {
  try {
    return sessionStorage.getItem("crown.jwt.access") || "";
  } catch { return ""; }
}

async function fetchNav() {
  const schoolId = getSchoolId();
  const token    = getToken();
  const headers  = {};
  if (schoolId) headers["X-School-Id"]    = schoolId;
  if (token)    headers["Authorization"]  = `Bearer ${token}`;

  const res = await fetch("/api/v1/nav/", { headers });
  if (!res.ok) throw new Error(`nav ${res.status}`);
  return res.json();
}

const FALLBACK_NAV = {
  groups: [
    {
      title: "Navigation",
      items: [{ label: "Home", href: "/admin" }],
    },
  ],
};

const BUILD_SHA = (import.meta?.env?.VITE_BUILD_SHA || "dev").slice(0, 7);
const DEPLOY_TAG = import.meta?.env?.VITE_DEPLOY_TAG || "";

export default function CrownLayout({ title, subtitle, right, children, mainClassName = "" }) {
  const [nav, setNav]         = useState(null);
  const [navError, setNavError] = useState(false);

  useEffect(() => {
    let mounted = true;
    fetchNav()
      .then((data) => { if (mounted) setNav(data); })
      .catch(()     => { if (mounted) setNavError(true); });
    return () => { mounted = false; };
  }, []);

  const activeNav = nav || (navError ? FALLBACK_NAV : null);
  const pathname  = typeof window !== "undefined" ? window.location.pathname : "";

  return (
    <div className="crown-app">
      <aside className="crown-sidebar">
        <h1>Crown</h1>
        <div className="crown-badge">
          {navError ? "Offline / Fallback" : "Demo / Internal"}
        </div>

        <nav style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 0 }}>
          {!activeNav && (
            <div style={{ fontSize: 12, opacity: 0.55, padding: "8px 10px" }}>
              Loading…
            </div>
          )}

          {activeNav?.groups?.map((group) => (
            <React.Fragment key={group.title}>
              <div
                style={{
                  fontSize: 9, fontWeight: 800, letterSpacing: 1.2,
                  textTransform: "uppercase", color: "rgba(255,255,255,0.35)",
                  padding: "10px 10px 2px", marginTop: 4,
                }}
              >
                {group.title}
              </div>

              {(group.items || []).map((item) => {
                const active = pathname === item.href;
                return (
                  <a
                    key={item.href}
                    href={item.href}
                    style={{
                      display: "block",
                      padding: "5px 10px",
                      borderRadius: 5,
                      fontSize: 13,
                      color: active ? "var(--crown-surface)" : "rgba(255,255,255,0.72)",
                      background: active ? "rgba(255,255,255,0.15)" : "transparent",
                      fontWeight: active ? 700 : 400,
                      textDecoration: "none",
                      transition: "background 0.1s",
                    }}
                  >
                    {item.label}
                  </a>
                );
              })}
            </React.Fragment>
          ))}
        </nav>
      </aside>

      <main className={`crown-main ${mainClassName}`.trim()}>
        {(title || subtitle || right) && (
          <div className="crown-pagehead">
            <div>
              {title    && <h2 className="crown-title">{title}</h2>}
              {subtitle && <p  className="crown-subtitle">{subtitle}</p>}
            </div>
            {right && <div>{right}</div>}
          </div>
        )}
        {children}
        <div style={{ marginTop: 24, paddingTop: 8, borderTop: "1px solid var(--crown-border)", fontSize: 11, color: "var(--crown-muted)", textAlign: "right" }}>
          Build: {BUILD_SHA}{DEPLOY_TAG ? ` · ${DEPLOY_TAG}` : ""}
        </div>
      </main>
    </div>
  );
}
