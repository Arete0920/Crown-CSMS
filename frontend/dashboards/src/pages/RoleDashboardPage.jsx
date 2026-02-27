/**
 * RoleDashboardPage — unified role-based dashboard.
 *
 * Route: /dash/:role  (e.g., /dash/admin, /dash/teacher)
 *
 * Fetches /api/dashboards/summary/ with the current school + role context,
 * renders widgets via WidgetDispatcher, and shows a DrilldownDrawer on expand.
 */
import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import WidgetDispatcher from "../components/dashboard/WidgetDispatcher.jsx";
import DrilldownDrawer from "../components/dashboard/DrilldownDrawer.jsx";
import { fetchDashboardSummary } from "../api/dashboards.js";

// Skeleton tile for loading state
function WidgetSkeleton() {
  return (
    <div
      className="crown-card"
      style={{
        height: 140,
        background: "linear-gradient(90deg, var(--crown-subtle) 25%, rgba(255,255,255,0.04) 50%, var(--crown-subtle) 75%)",
        backgroundSize: "400px 100%",
        animation: "crown-shimmer 1.4s ease infinite",
        borderRadius: "var(--crown-radius)",
      }}
      aria-label="Loading widget"
    />
  );
}

// Grid size → CSS grid-column span
const SIZE_COLS = { sm: "span 4", md: "span 6", lg: "span 12" };

function getSchoolId() {
  try { return sessionStorage.getItem("crown.school.id") || ""; }
  catch { return ""; }
}

export default function RoleDashboardPage() {
  const { role: routeRole } = useParams();
  const role = routeRole || "admin";

  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [widgets, setWidgets]   = useState([]);
  const [generatedAt, setGenAt] = useState(null);
  const [drawer, setDrawer]     = useState({ open: false, widget: null });

  const schoolId = getSchoolId();

  const load = useCallback(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    fetchDashboardSummary(schoolId, role).then(({ ok, data, error: err }) => {
      if (!mounted) return;
      if (ok && data?.widgets) {
        const sorted = [...data.widgets].sort((a, b) => (a.priority ?? 999) - (b.priority ?? 999));
        setWidgets(sorted);
        setGenAt(data.generated_at ?? null);
      } else {
        setError(err || "Failed to load dashboard");
      }
      setLoading(false);
    });

    return () => { mounted = false; };
  }, [role, schoolId]);

  useEffect(load, [load]);

  const openDrawer = useCallback((widget) => {
    setDrawer({ open: true, widget });
  }, []);

  const closeDrawer = useCallback(() => {
    setDrawer({ open: false, widget: null });
  }, []);

  const roleLabel = role.charAt(0).toUpperCase() + role.slice(1);
  const subtitle  = generatedAt
    ? `Updated ${new Date(generatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
    : "Loading…";

  return (
    <CrownLayout
      title={`${roleLabel} Dashboard`}
      subtitle={subtitle}
      right={
        <button
          onClick={load}
          disabled={loading}
          aria-label="Refresh dashboard"
          style={{
            background: "none",
            border: "1px solid var(--crown-border)",
            borderRadius: 8,
            color: "var(--crown-muted)",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: 16,
            padding: "4px 12px",
          }}
        >
          ↻
        </button>
      }
    >
      {/* Error banner */}
      {error && (
        <div
          role="alert"
          style={{
            background: "rgba(255,93,93,0.12)",
            border: "1px solid var(--crown-danger)",
            borderRadius: 10,
            color: "var(--crown-danger)",
            padding: "10px 16px",
            marginBottom: 16,
            fontSize: 14,
          }}
        >
          {error}
        </div>
      )}

      {/* Widget grid */}
      <div
        data-testid="dashboard-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(12, 1fr)",
          gap: 16,
        }}
      >
        {loading
          ? [1, 2, 3, 4].map((k) => (
              <div key={k} style={{ gridColumn: "span 6" }}>
                <WidgetSkeleton />
              </div>
            ))
          : widgets.map((w) => (
              <div
                key={w.key}
                data-widget-key={w.key}
                style={{ gridColumn: SIZE_COLS[w.size] ?? "span 6" }}
              >
                <WidgetDispatcher
                  widget={w}
                  onExpand={w.drilldown?.enabled ? () => openDrawer(w) : undefined}
                />
              </div>
            ))}
      </div>

      {/* Drilldown drawer */}
      <DrilldownDrawer
        open={drawer.open}
        title={drawer.widget?.title ?? "Detail"}
        widget={drawer.widget?.key}
        schoolId={schoolId}
        onClose={closeDrawer}
      />

      {/* Shimmer keyframe — injected once */}
      <style>{`
        @keyframes crown-shimmer {
          0%  { background-position: -400px 0; }
          100%{ background-position: 400px 0; }
        }
      `}</style>
    </CrownLayout>
  );
}
