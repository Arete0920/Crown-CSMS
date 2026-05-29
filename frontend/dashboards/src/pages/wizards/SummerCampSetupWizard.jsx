import { useEffect, useMemo, useState } from "react";
import CrownLayout from "../../components/crown/CrownLayout.jsx";
import DashboardSection from "../../components/layout/DashboardSection.jsx";
import { fetchSummerCampWizard, submitSummerCampWizard } from "../../api/summerCampApi.js";

const STEPS = ["Program", "Registration", "Operations", "Review"];

const defaults = {
  camp_name: "",
  season_year: new Date().getFullYear(),
  season_label: "Summer",
  registration_window_open: true,
  allow_waitlist: true,
  auto_promote_waitlist: true,
  require_immunization_review: true,
  pickup_authorization_required: true,
  default_ratio_numerator: 1,
  default_ratio_denominator: 12,
  cancellation_policy: "",
};

export default function SummerCampSetupWizard() {
  const [step, setStep] = useState(0);
  const [data, setData] = useState(defaults);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedAt, setSavedAt] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const wizard = await fetchSummerCampWizard();
        if (!cancelled) {
          setData((previous) => ({ ...previous, ...(wizard.config || {}) }));
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const canGoNext = useMemo(() => {
    if (step !== 0) return true;
    return data.camp_name.trim().length > 0;
  }, [data.camp_name, step]);

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    setData((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  async function saveWizard() {
    setSaving(true);
    setError(null);
    try {
      await submitSummerCampWizard(data);
      setSavedAt(new Date().toLocaleString());
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <CrownLayout title="Summer Camp Setup Wizard">
      <DashboardSection title="Setup Wizard">
        <div style={{ marginBottom: 16 }}>
          {STEPS.map((label, index) => (
            <span key={label} style={{ marginRight: 10, fontWeight: index === step ? 700 : 400 }}>
              {index + 1}. {label}
            </span>
          ))}
        </div>

        {loading && <span>Loading wizard...</span>}
        {error && (
          <div style={{ color: "var(--crown-danger)", background: "var(--crown-danger-bg)", padding: "10px 14px", borderRadius: 4, marginBottom: 10 }}>
            {error}
          </div>
        )}

        {!loading && (
          <form onSubmit={(event) => event.preventDefault()}>
            {step === 0 && (
              <>
                <label htmlFor="camp_name">Camp Name</label>
                <input id="camp_name" name="camp_name" value={data.camp_name} onChange={updateField} style={{ display: "block", width: "100%", marginBottom: 10 }} />
                <label htmlFor="season_year">Season Year</label>
                <input id="season_year" name="season_year" type="number" value={data.season_year} onChange={updateField} style={{ display: "block", width: "100%", marginBottom: 10 }} />
                <label htmlFor="season_label">Season Label</label>
                <input id="season_label" name="season_label" value={data.season_label} onChange={updateField} style={{ display: "block", width: "100%", marginBottom: 10 }} />
              </>
            )}

            {step === 1 && (
              <>
                <label style={{ display: "block", marginBottom: 8 }}>
                  <input name="registration_window_open" type="checkbox" checked={data.registration_window_open} onChange={updateField} /> Registration Open
                </label>
                <label style={{ display: "block", marginBottom: 8 }}>
                  <input name="allow_waitlist" type="checkbox" checked={data.allow_waitlist} onChange={updateField} /> Allow Waitlist
                </label>
                <label style={{ display: "block", marginBottom: 8 }}>
                  <input name="auto_promote_waitlist" type="checkbox" checked={data.auto_promote_waitlist} onChange={updateField} /> Auto Promote Waitlist
                </label>
                <label htmlFor="cancellation_policy">Cancellation Policy</label>
                <textarea id="cancellation_policy" name="cancellation_policy" value={data.cancellation_policy} onChange={updateField} style={{ display: "block", width: "100%", minHeight: 120 }} />
              </>
            )}

            {step === 2 && (
              <>
                <label style={{ display: "block", marginBottom: 8 }}>
                  <input name="require_immunization_review" type="checkbox" checked={data.require_immunization_review} onChange={updateField} /> Require Immunization Review
                </label>
                <label style={{ display: "block", marginBottom: 8 }}>
                  <input name="pickup_authorization_required" type="checkbox" checked={data.pickup_authorization_required} onChange={updateField} /> Pickup Authorization Required
                </label>
                <label htmlFor="default_ratio_numerator">Default Ratio (numerator)</label>
                <input id="default_ratio_numerator" name="default_ratio_numerator" type="number" value={data.default_ratio_numerator} onChange={updateField} style={{ display: "block", width: "100%", marginBottom: 10 }} />
                <label htmlFor="default_ratio_denominator">Default Ratio (denominator)</label>
                <input id="default_ratio_denominator" name="default_ratio_denominator" type="number" value={data.default_ratio_denominator} onChange={updateField} style={{ display: "block", width: "100%", marginBottom: 10 }} />
              </>
            )}

            {step === 3 && (
              <pre style={{ background: "var(--crown-surface-muted)", border: "1px solid var(--crown-border)", borderRadius: 6, padding: 12, overflowX: "auto" }}>
                {JSON.stringify(data, null, 2)}
              </pre>
            )}

            <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
              <button type="button" onClick={() => setStep((current) => Math.max(0, current - 1))} disabled={step === 0}>
                Back
              </button>
              <button type="button" onClick={() => setStep((current) => Math.min(STEPS.length - 1, current + 1))} disabled={!canGoNext || step === STEPS.length - 1}>
                Next
              </button>
              <button type="button" onClick={saveWizard} disabled={saving}>
                {saving ? "Saving..." : "Save Setup"}
              </button>
            </div>

            {savedAt && (
              <div style={{ marginTop: 10, color: "var(--crown-success)" }}>
                Saved at {savedAt}
              </div>
            )}
          </form>
        )}
      </DashboardSection>
    </CrownLayout>
  );
}
