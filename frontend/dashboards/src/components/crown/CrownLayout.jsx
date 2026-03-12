import React, { useEffect, useMemo, useState } from "react";

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

function getProfile() {
  try {
    const role =
      sessionStorage.getItem("crown.active.role") ||
      sessionStorage.getItem("crown.role") ||
      "Role";
    const displayName =
      sessionStorage.getItem("crown.user.name") ||
      sessionStorage.getItem("crown.user.email") ||
      "User";
    return { role, displayName };
  } catch {
    return { role: "Role", displayName: "User" };
  }
}

function buildBreadcrumb(pathname) {
  const cleanPath = (pathname || "/").split("?")[0].split("#")[0];
  const parts = cleanPath.split("/").filter(Boolean);
  if (!parts.length) {
    return [{ label: "Home", href: "/" }];
  }

  const crumbs = [{ label: "Home", href: "/" }];
  let acc = "";
  parts.forEach((part) => {
    acc += `/${part}`;
    const label = part
      .replace(/[-_]+/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    crumbs.push({ label, href: acc });
  });

  return crumbs;
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
  const [nav, setNav]           = useState(null);
  const [navError, setNavError] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    fetchNav()
      .then((data) => { if (mounted) setNav(data); })
      .catch(()     => { if (mounted) setNavError(true); });
    return () => { mounted = false; };
  }, []);

  const activeNav = nav || (navError ? FALLBACK_NAV : null);
  const pathname  = typeof window !== "undefined" ? window.location.pathname : "";
  const breadcrumbs = useMemo(() => buildBreadcrumb(pathname), [pathname]);
  const navGroups = activeNav?.groups || [];
  const hasNavItems = navGroups.some((group) => (group.items || []).length > 0);
  const profile = getProfile();

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  return (
    <div className="crown-app">
      <button
        type="button"
        className="crown-sidebar-toggle"
        onClick={() => setSidebarOpen((v) => !v)}
        aria-label="Toggle navigation"
      >
        Menu
      </button>

      {sidebarOpen ? (
        <button
          type="button"
          className="crown-sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation"
        />
      ) : null}

      <aside className={`crown-sidebar ${sidebarOpen ? "is-open" : ""}`.trim()}>
        <div className="crown-sidebar-header">
          <h1>Crown</h1>
          <button
            type="button"
            className="crown-sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            x
          </button>
        </div>

        <div className="crown-badge">
          {navError ? "Offline / Fallback" : "Live / Role Scoped"}
        </div>

        <nav style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 0 }}>
          {!activeNav && (
            <>
              <div style={{ fontSize: 12, opacity: 0.55, padding: "8px 10px" }}>
                Loading navigation...
              </div>
              <div className="crown-nav-skeleton" />
              <div className="crown-nav-skeleton" />
              <div className="crown-nav-skeleton" />
            </>
          )}

          {activeNav && !hasNavItems ? (
            <div style={{ fontSize: 12, opacity: 0.7, padding: "8px 10px" }}>
              No navigation items are available for this role.
            </div>
          ) : null}

          {navGroups.map((group) => (
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
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "4px 0 8px" }}>
          <div className="crown-utility-row" style={{ marginBottom: 10, alignItems: "center" }}>
            <div className="crown-breadcrumbs" aria-label="Breadcrumb" style={{ fontSize: 12, opacity: 0.9 }}>
            {breadcrumbs.map((crumb, index) => {
              const isLast = index === breadcrumbs.length - 1;
              return (
                <span key={crumb.href} className="crown-breadcrumb-item">
                  {isLast ? (
                    <span>{crumb.label}</span>
                  ) : (
                    <a href={crumb.href}>{crumb.label}</a>
                  )}
                  {!isLast ? <span className="crown-breadcrumb-sep">/</span> : null}
                </span>
              );
            })}
          </div>

            <div className="crown-utility-actions" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span className="crown-pill">Notifications</span>
            <span className="crown-pill">{profile.role}</span>
            <span className="crown-pill">{profile.displayName}</span>
          </div>
        </div>

          {(title || subtitle || right) && (
            <div className="crown-pagehead" style={{ marginBottom: 14, alignItems: "flex-start" }}>
              <div style={{ paddingTop: 2 }}>
              {title    && <h2 className="crown-title">{title}</h2>}
              {subtitle && <p  className="crown-subtitle">{subtitle}</p>}
            </div>
              {right && <div style={{ paddingTop: 2 }}>{right}</div>}
            </div>
          )}

          {navError ? (
            <div className="crown-global-notice" role="status" style={{ marginBottom: 12 }}>
              Navigation service unavailable. Showing fallback menu.
            </div>
          ) : null}

          <div style={{ paddingTop: 4 }}>
            {children}
          </div>
        </div>

        <div style={{ marginTop: 28, paddingTop: 10, borderTop: "1px solid var(--crown-border)", fontSize: 11, color: "var(--crown-muted)", textAlign: "right" }}>
          Build: {BUILD_SHA}{DEPLOY_TAG ? ` · ${DEPLOY_TAG}` : ""}
        </div>
      </main>
    </div>
  );
}
