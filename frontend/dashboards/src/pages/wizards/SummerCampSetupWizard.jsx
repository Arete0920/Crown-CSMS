import { useEffect, useMemo, useState } from "react";
import CrownLayout from "../../components/crown/CrownLayout.jsx";
import DashboardSection from "../../components/layout/DashboardSection.jsx";
import { fetchSummerCampWizard, submitSummerCampWizard } from "../../api/summerCampApi.js";

import { CAMP_SETUP_KEYS, CAMP_WIZARD_STEPS, readCampSetup, readCampWizardState, verifyCampSetupReadback } from "./campSetupReadback.js";

const STEPS = CAMP_WIZARD_STEPS;

const defaults = {
  camp_name: "Summer Camp",
  default_capacity: 30,
  default_staff_ratio: 10,
  public_registration_enabled: false,
  billing_policy: "PER_SESSION",
};
const CONFIG_KEYS = CAMP_SETUP_KEYS;


export default function SummerCampSetupWizard() {
  const [step, setStep] = useState(0);
  const [data, setData] = useState(defaults);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedAt, setSavedAt] = useState("");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const wizard = await fetchSummerCampWizard();
        if (!cancelled) {
          const config = readCampSetup(wizard);
          const progress = readCampWizardState(wizard);
          setData(config);
          // Reopen at the last persisted step instead of silently restarting
          // from Program and overwriting valid completion progress on Save.
          setStep(Math.max(0, progress.completed_steps.length - 1));
          setLoaded(true);
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

  function changeStep(direction) {
    // A successful readback applies only to the configuration and wizard
    // progress actually submitted, not to a subsequently selected step.
    setSavedAt("");
    setStep((current) => Math.max(0, Math.min(STEPS.length - 1, current + direction)));
  }

  function updateField(event) {
    setSavedAt("");
    const { name, value, type, checked } = event.target;
    setData((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : type === "number" ? Number(value) : value,
    }));
  }

  async function saveWizard() {
    if (!loaded || saving) return;
    setSavedAt("");
    // Invalid edits have not touched the server. Keep the form available
    // for correction instead of claiming an uncertain network write.
    const submitted = {
      config: Object.fromEntries(CONFIG_KEYS.map((key) => [key, data[key]])),
      completed_steps: STEPS.slice(0, step + 1),
      is_completed: step === STEPS.length - 1,
    };
    submitted.config.camp_name = submitted.config.camp_name.trim();
    try {
      readCampSetup(submitted);
    } catch {
      setError("Correct the camp name, positive whole-number capacity and staff ratio, and registration/billing settings. Nothing was submitted.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await submitSummerCampWizard(submitted);
      const readback = await fetchSummerCampWizard();
      setData(verifyCampSetupReadback(readback, submitted));
      setSavedAt(new Date().toLocaleString());
    } catch (e) {
      setLoaded(false);
      setError(`${e.message} Reload this page to verify the current server state before saving again.`);
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
          <div role="alert" style={{ color: "var(--crown-danger)", background: "var(--crown-danger-bg)", padding: "10px 14px", borderRadius: 4, marginBottom: 10 }}>
            {error}
          </div>
        )}

        {!loading && loaded && (
          <form onSubmit={(event) => event.preventDefault()}>
            <fieldset disabled={saving}>
              <legend>Camp configuration</legend>
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
              <dl>
                <dt>Camp name</dt><dd>{data.camp_name}</dd>
                <dt>Session capacity</dt><dd>{data.default_capacity}</dd>
                <dt>Maximum campers per staff member</dt><dd>{data.default_staff_ratio}</dd>
                <dt>Public registration</dt><dd>{data.public_registration_enabled ? "Enabled in configuration" : "Disabled"}</dd>
                <dt>Billing policy</dt><dd>{{ PER_SESSION: "Per session", PER_WEEK: "Per week", FULL_CAMP: "Full camp" }[data.billing_policy]}</dd>
              </dl>
            )}

            <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
              <button type="button" onClick={() => changeStep(-1)} disabled={step === 0}>
                Back
              </button>
              <button type="button" onClick={() => changeStep(1)} disabled={!canGoNext || step === STEPS.length - 1}>
                Next
              </button>
              <button type="button" onClick={saveWizard} disabled={saving}>
                {saving ? "Saving..." : "Save Setup"}
              </button>
            </div>

            </fieldset>
            {savedAt && (
              <div style={{ marginTop: 10, color: "var(--crown-success)" }}>
                Saved and verified against server records at {savedAt}
              </div>
            )}
          </form>
        )}
      </DashboardSection>
    </CrownLayout>
  );
}
