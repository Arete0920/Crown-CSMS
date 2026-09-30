import React, { useEffect, useMemo, useState } from "react";
import { authenticatedFetch } from "../../utils/authClient.js";
import "../../styles/operational-dashboard-canonical.css";

/**
 * CrownLayout app shell with permission-derived sidebar + main content area.
 *
 * Props:
 *   title     page heading (h2)
 *   subtitle  secondary line under heading (muted)
 *   right     JSX slotted to the top-right of the page header
 *   children  page body
 */

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
    return { role: toRoleLabel(role), displayName };
  } catch {
    return { role: "Role", displayName: "User" };
  }
}

function toRoleLabel(role) {
  const value = String(role || "").trim();
  if (!value) return "Role";
  if (value.toLowerCase() === "admin") return "School Administrator";
  if (value.toLowerCase() === "school_admin") return "School Administrator";
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
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
  const res = await authenticatedFetch("/api/v1/nav/");
  return res.json();
}

const EMPTY_ROLE_SCOPED_NAV = Object.freeze({ groups: [] });
const CANONICAL_OPERATIONAL_DASHBOARD_PATHS = new Set([
  "/academic-support",
  "/communications-director",
  "/library",
  "/pd",
  "/security",
  "/student-services",
]);

function normalizeRoleScopedNav(navData) {
  const incoming = Array.isArray(navData?.groups) ? navData.groups : [];
  const seen = new Set();

  const groups = incoming.map((group) => {
    const items = Array.isArray(group?.items)
      ? group.items.filter((item) => {
          const href = String(item?.href || "").trim();
          if (!href || seen.has(href)) return false;
          seen.add(href);
          return true;
        })
      : [];

    return { ...group, items };
  }).filter((group) => group.items.length > 0);

  return {
    ...navData,
    groups,
  };
}

const BUILD_SHA = (import.meta?.env?.VITE_BUILD_SHA || "dev").slice(0, 7);
const DEPLOY_TAG = import.meta?.env?.VITE_DEPLOY_TAG || "";

export default function CrownLayout({ title, subtitle, right, children, mainClassName = "", publicMode = false }) {
  const [nav, setNav] = useState(null);
  const [navError, setNavError] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (publicMode) {
      setNav(EMPTY_ROLE_SCOPED_NAV);
      setNavError(false);
      return undefined;
    }
    let mounted = true;
    fetchNav()
      .then((data) => {
        if (mounted) {
          setNav(normalizeRoleScopedNav(data));
          setNavError(false);
        }
      })
      .catch(() => {
        if (mounted) {
          setNav(null);
          setNavError(true);
        }
      });
    return () => { mounted = false; };
  }, [publicMode]);

  const activeNav = nav || (navError ? EMPTY_ROLE_SCOPED_NAV : null);
  const pathname = typeof window !== "undefined" ? globalThis.location.pathname : "";
  const breadcrumbs = useMemo(() => buildBreadcrumb(pathname), [pathname]);
  const navGroups = activeNav?.groups || [];
  const hasNavItems = navGroups.some((group) => (group.items || []).length > 0);
  const profile = getProfile();
  const operationalLayoutClass = CANONICAL_OPERATIONAL_DASHBOARD_PATHS.has(pathname)
    ? "crown-operational-canonical"
    : "";

  return (
    <div className="crown-app">
      {!publicMode && <button
        type="button"
        className="crown-sidebar-toggle"
        onClick={() => setSidebarOpen((v) => !v)}
        aria-label="Toggle navigation"
      >
        Menu
      </button>}

      {!publicMode && sidebarOpen ? (
        <button
          type="button"
          className="crown-sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation"
        />
      ) : null}

      {!publicMode && <aside
        className={`crown-sidebar ${sidebarOpen ? "is-open" : ""}`.trim()}
        style={{
          background: "linear-gradient(180deg, var(--crown-primary-strong), var(--crown-primary-deep))",
          color: "var(--crown-surface)",
        }}
      >
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
          {navError ? "Navigation Unavailable" : "Live / Role Scoped"}
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
              {navError
                ? "Role-scoped navigation is temporarily unavailable."
                : "No navigation items are available for this role."}
            </div>
          ) : null}

          {navGroups.map((group) => (
            <React.Fragment key={group.title}>
              <div
                style={{
                  fontSize: 9, fontWeight: 800, letterSpacing: 1.2,
                  textTransform: "uppercase", color: "var(--crown-compat-color-b287e65b63)",
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
                      color: active ? "var(--crown-surface)" : "var(--crown-compat-color-b287e65b63)",
                      background: active ? "var(--crown-compat-color-5089217ef2)" : "transparent",
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
      </aside>}

      <main
        className={`crown-main ${operationalLayoutClass} ${mainClassName}`.trim()}
        style={publicMode ? { marginLeft: 0 } : undefined}
      >
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "4px 0 8px" }}>
          {!publicMode && <div className="crown-utility-row" style={{ marginBottom: 10, alignItems: "center" }}>
            <div className="crown-breadcrumbs" aria-label="Breadcrumb" style={{ fontSize: 12, opacity: 0.9 }}>
            {breadcrumbs.map((crumb, index) => {
              const isLast = index === breadcrumbs.length - 1;
              return (
                <span key={crumb.href} className="crown-breadcrumb-item">
                  {isLast ? (
                    <span>{crumb.label}</span>
                  ) : (
                    <a
                      href={crumb.href}
                      style={{
                        color: "var(--crown-primary-deep)",
                        fontWeight: 700,
                        textDecoration: "underline",
                        textUnderlineOffset: "2px",
                      }}
                    >
                      {crumb.label}
                    </a>
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
              {title && <h2 className="crown-title">{title}</h2>}
              {subtitle && <p className="crown-subtitle">{subtitle}</p>}
            </div>
              {right && <div style={{ paddingTop: 2 }}>{right}</div>}
            </div>
          )}

          {!publicMode && navError ? (
            <div className="crown-global-notice" role="status" style={{ marginBottom: 12 }}>
              Navigation service unavailable. Role-scoped navigation is hidden until the service recovers.
            </div>
          ) : null}

          <div style={{ paddingTop: 4 }}>
            {children}
          </div>
        </div>

        <div style={{ marginTop: 28, paddingTop: 10, borderTop: "1px solid var(--crown-border)", fontSize: 11, color: "var(--crown-muted)", textAlign: "right" }}>
          Build: {BUILD_SHA}{DEPLOY_TAG ? `  ${DEPLOY_TAG}` : ""}
        </div>
      </main>
    </div>
  );
}
