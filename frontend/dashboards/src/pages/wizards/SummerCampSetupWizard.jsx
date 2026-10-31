import { useEffect, useMemo, useState } from "react";
import CrownLayout from "../../components/crown/CrownLayout.jsx";
import DashboardSection from "../../components/layout/DashboardSection.jsx";
import { fetchSummerCampWizard, submitSummerCampWizard } from "../../api/summerCampApi.js";

const STEPS = ["Program", "Registration", "Operations", "Review"];

const defaults = {
  camp_name: "Summer Camp",
  default_capacity: 30,
  default_staff_ratio: 10,
  public_registration_enabled: false,
  billing_policy: "PER_SESSION",
};
const CONFIG_KEYS = Object.keys(defaults);


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
          setData((previous) => ({
            ...previous,
            ...Object.fromEntries(CONFIG_KEYS.filter((key) => wizard.config?.[key] !== undefined).map((key) => [key, wizard.config[key]])),
          }));
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
      [name]: type === "checkbox" ? checked : type === "number" ? Number(value) : value,
    }));
  }

  async function saveWizard() {
    setSaving(true);
    setError(null);
    try {
      await submitSummerCampWizard({
        config: Object.fromEntries(CONFIG_KEYS.map((key) => [key, data[key]])),
        completed_steps: STEPS.slice(0, step + 1),
        is_completed: step === STEPS.length - 1,
      });
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
              </>
            )}

            {step === 1 && (
              <>
                <label style={{ display: "block", marginBottom: 8 }}>
                  <input name="public_registration_enabled" type="checkbox" checked={data.public_registration_enabled} onChange={updateField} /> Public Registration Enabled
                </label>
                <label htmlFor="billing_policy">Billing Policy</label>
                <select id="billing_policy" name="billing_policy" value={data.billing_policy} onChange={updateField} style={{ display: "block", marginBottom: 10 }}>
                  <option value="PER_SESSION">Per Session</option>
                  <option value="PER_WEEK">Per Week</option>
                  <option value="FULL_CAMP">Full Camp</option>
                </select>
              </>
            )}

            {step === 2 && (
              <>
                <label htmlFor="default_capacity">Default Session Capacity</label>
                <input id="default_capacity" name="default_capacity" type="number" min="1" value={data.default_capacity} onChange={updateField} style={{ display: "block", width: "100%", marginBottom: 10 }} />
                <label htmlFor="default_staff_ratio">Maximum Campers per Staff Member</label>
                <input id="default_staff_ratio" name="default_staff_ratio" type="number" min="1" value={data.default_staff_ratio} onChange={updateField} style={{ display: "block", width: "100%", marginBottom: 10 }} />
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
