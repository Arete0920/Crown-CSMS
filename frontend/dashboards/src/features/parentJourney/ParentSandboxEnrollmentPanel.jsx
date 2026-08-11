import { useEffect, useState } from "react";
import {
  completeSandboxParentEnrollment,
  loadParentJourneyOverview,
  loadSandboxParentEnrollment,
} from "./parentJourneyState.js";

const IS_SANDBOX = Boolean(
  import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1"
);

function statusText(state) {
  if (!state) return "Loading accepted enrollment scenario…";
  if (state.lifecycle_stage === "enrolled") {
    return `${state.child_name || "Student"} is enrolled and the resulting student context is active.`;
  }
  return `${state.child_name || "Accepted student"} is ready for enrollment acceptance.`;
}

export default function ParentSandboxEnrollmentPanel() {
  const [state, setState] = useState(null);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!IS_SANDBOX) return undefined;
    let active = true;
    loadSandboxParentEnrollment()
      .then((payload) => {
        if (active) setState(payload);
      })
      .catch((err) => {
        if (active) setError(err?.response?.data?.detail || err?.message || "Enrollment scenario unavailable.");
      });
    return () => {
      active = false;
    };
  }, []);

  if (!IS_SANDBOX) return null;

  async function completeEnrollment() {
    if (!state?.application_id || !acceptedTerms) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const completed = await completeSandboxParentEnrollment(state.application_id, true);
      if (completed.demo_payment_processed !== false) {
        throw new Error("Sandbox payment boundary was not preserved.");
      }
      if (completed.lifecycle_stage !== "enrolled" || !completed.child_id) {
        throw new Error("Enrollment did not produce the expected student context.");
      }
      setState(completed);
      const overview = await loadParentJourneyOverview({ force: true });
      const applications = overview?.admissions_continuity?.applications || [];
      const sameApplication = applications.find(
        (application) => String(application.application_id) === String(completed.application_id)
      );
      if (!sameApplication || sameApplication.lifecycle_stage !== "enrolled") {
        throw new Error("Parent360 did not reflect the enrolled application after reload.");
      }
      setMessage("Enrollment completed and verified in Parent360. No external payment was processed.");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Enrollment could not be completed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="learning-authority-card" aria-label="Sandbox parent enrollment transaction" data-testid="sandbox-parent-enrollment-panel">
      <div className="crown-section-heading">
        <div>
          <p className="crown-eyebrow">Accepted family workflow</p>
          <h2>Enrollment acceptance</h2>
          <p>{statusText(state)}</p>
        </div>
      </div>

      {error ? <div className="sandbox-message is-warning" role="alert">{error}</div> : null}
      {message ? <div className="sandbox-message is-info" role="status">{message}</div> : null}

      {state ? (
        <div className="learning-authority-grid">
          <article><strong>Contract</strong><p>{state.contract_status}</p></article>
          <article><strong>Deposit</strong><p>{state.deposit_status}</p></article>
          <article><strong>Student record</strong><p>{state.applicant_to_student_status}</p></article>
          <article><strong>Parent portal</strong><p>{state.parent_portal_activation_status}</p></article>
        </div>
      ) : null}

      {state?.lifecycle_stage !== "enrolled" ? (
        <div style={{ marginTop: 18 }}>
          <label>
            <input
              type="checkbox"
              aria-label="Accept sandbox enrollment agreement"
              checked={acceptedTerms}
              onChange={(event) => setAcceptedTerms(event.target.checked)}
              disabled={busy}
            />{" "}
            I accept the demonstration enrollment agreement for this fictional Heritage applicant.
          </label>
          <p style={{ marginTop: 8 }}>
            Sandbox demonstration: the deposit settlement and school countersign are simulated after your acceptance. No payment provider is called and no money is moved.
          </p>
          <button
            type="button"
            className="crown-btn crown-btn-primary"
            onClick={completeEnrollment}
            disabled={!acceptedTerms || busy || !state?.application_id}
          >
            {busy ? "Completing enrollment…" : "Accept enrollment and complete demo handoff"}
          </button>
        </div>
      ) : (
        <p data-testid="sandbox-parent-enrollment-complete">
          Resulting student: <strong>{state.child_name}</strong>. Classroom readiness and Parent portal activation are {state.classroom_readiness_status} / {state.parent_portal_activation_status}.
        </p>
      )}
    </section>
  );
}
