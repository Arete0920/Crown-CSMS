/**
 * WizardHub — Crown2026
 * =====================
 * Fetches all registered wizards from GET /api/v1/wizards/ and renders
 * a navigable card list. Browser paths are sourced from WIZARD_MANIFEST
 * (the frontend's side of the drift contract).
 *
 * Route: /wizards
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { fetchWizards } from "../api/wizards";
import { WIZARD_MANIFEST } from "../routes/wizard-manifest.js";

// Build slug → path lookup once (manifest is static)
const SLUG_TO_PATH = Object.fromEntries(
  WIZARD_MANIFEST.map((w) => [w.slug, w.path])
);

export default function WizardHub() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [items, setItems] = useState([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setErr("");
        const data = await fetchWizards();
        const wizards = Array.isArray(data?.wizards) ? data.wizards : [];
        if (alive) setItems(wizards);
      } catch (e) {
        if (alive) setErr(e?.message || "Failed to load wizards.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const enabled = useMemo(() => items.filter((w) => w?.enabled), [items]);

  if (loading) {
    return (
      <CrownLayout title="Wizard Hub" subtitle="Setup wizards">
        <p style={{ opacity: 0.7 }}>Loading wizards…</p>
      </CrownLayout>
    );
  }

  if (err) {
    return (
      <CrownLayout title="Wizard Hub" subtitle="Setup wizards">
        <p style={{ color: "var(--crown-danger)" }}>Error: {err}</p>
      </CrownLayout>
    );
  }

  return (
    <CrownLayout
      title="Wizard Hub"
      subtitle={`${enabled.length} setup wizard${enabled.length !== 1 ? "s" : ""} available`}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: 12,
        }}
      >
        {enabled.map((w) => {
          const browserPath = SLUG_TO_PATH[w.slug];
          return (
            <div
              key={w.slug}
              style={{
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 12,
                padding: "14px 16px",
                background: "rgba(255,255,255,0.04)",
              }}
            >
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{w.title}</div>
              <div
                style={{
                  fontSize: 12,
                  opacity: 0.55,
                  fontFamily: "monospace",
                  marginBottom: 12,
                }}
              >
                {w.slug}
              </div>
              {browserPath ? (
                <Link
                  to={browserPath}
                  style={{ fontSize: 14, textDecoration: "underline" }}
                >
                  Open wizard →
                </Link>
              ) : (
                <span style={{ fontSize: 13, opacity: 0.45 }}>
                  (path not in manifest)
                </span>
              )}
            </div>
          );
        })}
      </div>
    </CrownLayout>
  );
}
