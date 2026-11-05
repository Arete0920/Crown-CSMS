import { useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";
import {
  getAccessToken,
  getSelectedSchoolId,
  SCHOOL_CONTEXT_CHANGE_EVENT,
} from "../utils/authClient";
import ParentJourneyOverviewPage from "../features/parentJourney/ParentJourneyOverviewPage.jsx";
import CrownDashboardShell from "../components/crown-dashboard/CrownDashboardShell.jsx";
import { getDashboardTemplate } from "../config/dashboardTemplates/index.js";

const ENDPOINT = "/api/v1/aid/family/demo-intake/";
// Shared token-change event added by the separate Diadem auth-hardening PR.
// This listener is compatible with that PR and does not modify shared auth code.
const AUTH_CONTEXT_CHANGE_EVENT = "crown:auth-context-changed";
const UNKNOWN_WRITE_MESSAGE =
  "The fictional submission may have been accepted, but its saved status could not be verified. " +
  "Refresh the application status before proceeding. Do not submit it again.";

function identitySnapshot() {
  return { school: getSelectedSchoolId(), token: getAccessToken() };
}

function identityMatches(left, right) {
  return left?.school === right?.school && left?.token === right?.token;
}

function errorMessage(error) {
  const data = error?.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  return error instanceof Error ? error.message : "The request could not be completed.";
}

function FictionalFinancialAidPage({ hosted = false }) {
  const endpoint = hosted ? "/api/v1/buyer-demo/jireh/aid/family/" : ENDPOINT;
  const parentShell = getDashboardTemplate("parent");
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [yearId, setYearId] = useState("");
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [scenario, setScenario] = useState("");
  const [householdSize, setHouseholdSize] = useState("3");
  const [acknowledged, setAcknowledged] = useState(false);
  const [needsReconciliation, setNeedsReconciliation] = useState(false);

  const mountedRef = useRef(false);
  const revisionRef = useRef(0);
  const identityRef = useRef(identitySnapshot());
  const syncIdentityRef = useRef(() => {});

  function current(origin, revision) {
    return mountedRef.current
      && revisionRef.current === revision
      && identityMatches(origin, identityRef.current)
      && identityMatches(origin, identitySnapshot());
  }

  function discardStale(origin, revision) {
    if (current(origin, revision)) return false;
    // The event may not exist on older feature branches; a response boundary
    // still notices the changed token/school and clears the old household.
    syncIdentityRef.current();
    return true;
  }

  async function readback(origin, revision) {
    const response = await apiFetch(endpoint);
    let data = await response.json();
    if (discardStale(origin, revision)) return null;
    if (
      data?.demo_only !== true
      || !Array.isArray(data.academic_years)
      || !Array.isArray(data.students)
      || !Array.isArray(data.scenarios)
      || !Array.isArray(data.applications)
    ) {
      throw new Error("The fictional Financial Aid readback returned an invalid contract.");
    }
    if (hosted) {
      if (data.synthetic_only !== true || typeof data.household !== "string") {
        throw new Error("The hosted fictional household could not be verified.");
      }
      data = { ...data, household_name: data.household, applications: data.applications.map((app) => ({
        ...app, academic_year_name: data.academic_years.find((year) => year.id === app.academic_year_id)?.name || app.academic_year_id,
      })) };
    }
    setRecord(data);
    setYearId((previous) =>
      data.academic_years.some((year) => year.id === previous)
        ? previous : data.academic_years[0]?.id || ""
    );
    setScenario((previous) =>
      data.scenarios.some((item) => item.id === previous)
        ? previous : data.scenarios[0]?.id || ""
    );
    return data;
  }

  useEffect(() => {
    mountedRef.current = true;

    async function reload(origin, revision) {
      setLoading(true);
      try {
        const data = await readback(origin, revision);
        if (!data || discardStale(origin, revision)) return;
        setSelectedStudents(data.students.length === 1 ? [data.students[0].id] : []);
        setLoading(false);
      } catch (failure) {
        if (discardStale(origin, revision)) return;
        setError(errorMessage(failure));
        setLoading(false);
      }
    }

    function syncIdentity() {
      const next = identitySnapshot();
      if (identityMatches(identityRef.current, next)) return;
      identityRef.current = next;
      revisionRef.current += 1;
      setRecord(null);
      setYearId("");
      setScenario("");
      setSelectedStudents([]);
      setHouseholdSize("3");
      setAcknowledged(false);
      setConfirmation("");
      setError("");
      setSaving(false);
      setNeedsReconciliation(false);
      void reload(next, revisionRef.current);
    }

    syncIdentityRef.current = syncIdentity;
    void reload(identityRef.current, revisionRef.current);
    window.addEventListener(SCHOOL_CONTEXT_CHANGE_EVENT, syncIdentity);
    window.addEventListener(AUTH_CONTEXT_CHANGE_EVENT, syncIdentity);
    window.addEventListener("storage", syncIdentity);
    window.addEventListener("focus", syncIdentity);
    window.addEventListener("pageshow", syncIdentity);
    return () => {
      mountedRef.current = false;
      revisionRef.current += 1;
      syncIdentityRef.current = () => {};
      window.removeEventListener(SCHOOL_CONTEXT_CHANGE_EVENT, syncIdentity);
      window.removeEventListener(AUTH_CONTEXT_CHANGE_EVENT, syncIdentity);
      window.removeEventListener("storage", syncIdentity);
      window.removeEventListener("focus", syncIdentity);
      window.removeEventListener("pageshow", syncIdentity);
    };
  }, []);

  function clearSuccess() {
    setConfirmation("");
  }

  function toggleStudent(studentId) {
    clearSuccess();
    setSelectedStudents((currentStudents) =>
      currentStudents.includes(studentId)
        ? currentStudents.filter((id) => id !== studentId)
        : [...currentStudents, studentId]
    );
  }

  const existing = record?.applications?.find(
    (application) => String(application.academic_year_id) === String(yearId)
  );

  async function submit(event) {
    event.preventDefault();
    if (saving || existing || needsReconciliation) return;
    const origin = identitySnapshot();
    const revision = revisionRef.current;
    if (discardStale(origin, revision)) return;

    const requestedYear = yearId;
    const requestedStudents = [...selectedStudents].map(String);
    setError("");
    setConfirmation("");
    setSaving(true);
    let accepted = false;
    let attempted = false;
    try {
      attempted = true;
      const response = await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify({
          academic_year_id: requestedYear,
          student_ids: requestedStudents,
          household_size: Number(householdSize),
          scenario,
          fictional_acknowledged: acknowledged,
        }),
      });
      const result = await response.json();
      if (discardStale(origin, revision)) return;
      const submitted = result?.application;
      if (result?.demo_only !== true || !submitted?.id) {
        throw new Error("The fictional submission did not return a verifiable application.");
      }
      accepted = true;

      // A POST response is not proof of saved or correctly scoped family data.
      // Do not present success until a separate read verifies all identifiers.
      const refreshed = await readback(origin, revision);
      if (!refreshed || discardStale(origin, revision)) return;
      const saved = refreshed.applications.find(
        (application) => String(application.id) === String(submitted.id)
      );
      const savedStudents = Array.isArray(saved?.student_ids) ? saved.student_ids.map(String) : [];
      if (
        !saved
        || saved.status !== "SUBMITTED"
        || !saved.submitted_at
        || String(saved.academic_year_id) !== String(requestedYear)
        || savedStudents.length !== requestedStudents.length
        || !requestedStudents.every((id) => savedStudents.includes(id))
      ) {
        throw new Error("Independent saved-record verification failed.");
      }
      setNeedsReconciliation(false);
      setConfirmation("Fictional application #" + saved.id + " submitted and independently verified.");
    } catch (failure) {
      if (discardStale(origin, revision)) return;
      // A transport error or server failure after dispatch can mean the
      // server committed despite the missing response. Never auto-retry.
      if (accepted || (attempted && (!Number.isInteger(failure?.status) || failure.status >= 500))) {
        setNeedsReconciliation(true);
        setError(UNKNOWN_WRITE_MESSAGE);
      } else {
        setError(errorMessage(failure));
      }
    } finally {
      if (!discardStale(origin, revision)) setSaving(false);
    }
  }

  async function refreshStatus() {
    const origin = identitySnapshot();
    const revision = revisionRef.current;
    if (discardStale(origin, revision) || saving) return;
    setError("");
    setConfirmation("");
    try {
      const data = await readback(origin, revision);
      if (!data || discardStale(origin, revision)) return;
      if (needsReconciliation) {
        const found = data.applications.some(
          (application) => String(application.academic_year_id) === String(yearId)
        );
        if (found) setNeedsReconciliation(false);
        else setError(UNKNOWN_WRITE_MESSAGE);
      }
    } catch (failure) {
      if (!discardStale(origin, revision)) setError(errorMessage(failure));
    }
  }

  return (
    <CrownDashboardShell
      activePath="/parent/financial-aid"
      schoolName={parentShell.schoolName}
      user={parentShell.user}
      updatesCount={parentShell.updatesCount}
    >
      <section className="crown-dashboard learning-workflow-page" data-testid="jireh-family-demo">
        <header className="crown-dashboard-hero">
          <div>
            <p className="crown-eyebrow">Jireh Financial Aid · school application</p>
            <h1>Family Financial Aid demonstration</h1>
            <p className="crown-dashboard-purpose">
              Submit a fictional application and review its saved status.
              This fictional demonstration is not a real Financial Aid application.
            </p>
          </div>
        </header>
        <section className="learning-authority-card" aria-label="Fictional financial aid application">
          <h2>Fictional household application</h2>
          <p><strong>Demo only.</strong> Never enter actual income, assets, liabilities,
            personal financial details, documents, or payment information.
            Only invented example scenarios are accepted.</p>
          {loading ? <p role="status">Loading authorized students and school year…</p> : null}
          {error ? <p role="alert" className="crown-alert--error">{error}</p> : null}
          {confirmation ? <p role="status" data-testid="jireh-submit-confirmation">{confirmation}</p> : null}
          {record ? (
            <>
              <p>Household: <strong>{record.household_name}</strong></p>
              <form onSubmit={submit}>
                <div className="learning-record-detail-block">
                  <label htmlFor="jireh-demo-year">Financial Aid year</label>
                  <select id="jireh-demo-year" value={yearId} onChange={(event) => { clearSuccess(); setYearId(event.target.value); }} disabled={saving} required>
                    {record.academic_years.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
                  </select>
                </div>
                <fieldset>
                  <legend>Students applying (select each student explicitly)</legend>
                  {record.students.length === 0 ? <p>No authorized students are available.</p> : null}
                  {record.students.map((student) => (
                    <label key={student.id} style={{ display: "block", margin: "8px 0" }}>
                      <input
                        type="checkbox"
                        checked={selectedStudents.includes(student.id)}
                        onChange={() => toggleStudent(student.id)}
                        disabled={Boolean(existing) || saving}
                      />
                      {" "}{student.name}
                    </label>
                  ))}
                </fieldset>
                <div className="learning-record-detail-block">
                  <label htmlFor="jireh-demo-size">Fictional household size</label>
                  <input
                    id="jireh-demo-size" type="number" min="1" max="20" step="1"
                    value={householdSize} onChange={(event) => { clearSuccess(); setHouseholdSize(event.target.value); }}
                    disabled={Boolean(existing) || saving} required
                  />
                </div>
                <div className="learning-record-detail-block">
                  <label htmlFor="jireh-demo-scenario">Fictional financial scenario</label>
                  <select
                    id="jireh-demo-scenario" value={scenario}
                    onChange={(event) => { clearSuccess(); setScenario(event.target.value); }}
                    disabled={Boolean(existing) || saving} required
                  >
                    {record.scenarios.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
                  </select>
                  <small>These examples are invented; the family does not enter financial figures.</small>
                </div>
                {!existing ? (
                  <label style={{ display: "block", margin: "16px 0" }}>
                    <input
                      type="checkbox" checked={acknowledged}
                      onChange={(event) => { clearSuccess(); setAcknowledged(event.target.checked); }}
                      disabled={saving}
                    />
                    {" "}I confirm all application information is fictional demonstration data.
                  </label>
                ) : null}
                {existing ? (
                  <p role="status">An application exists for this household and year. Duplicate submission is disabled.</p>
                ) : (
                  <button
                    type="submit"
                    disabled={saving || needsReconciliation || !acknowledged || !yearId || !scenario || selectedStudents.length === 0}
                  >
                    {saving ? "Submitting fictional application…" : "Submit fictional Financial Aid application"}
                  </button>
                )}
              </form>
              {needsReconciliation ? <p role="status">Submission outcome unresolved. Refresh the saved status before proceeding; do not submit again.</p> : null}
              <section aria-label="Saved Jireh applications" data-testid="jireh-saved-applications">
                <h2>{hosted ? "Saved fictional applications" : "Saved applications and offered awards"}</h2>
                {hosted && <p>No awards, eligibility decisions or funds are processed by this demonstration.</p>}
                {record.applications.length === 0 ? <p>No school Financial Aid applications submitted yet.</p> : null}
                {record.applications.map((application) => (
                  <article key={application.id} className="learning-record-detail-card">
                    <p><strong>Application #{application.id}</strong></p>
                    <p>Year: {application.academic_year_name} · Status: <strong>{application.status}</strong></p>
                    <p>Submitted: {application.submitted_at ? new Date(application.submitted_at).toLocaleString() : "Not submitted"}</p>
                    <p>Selected applicant students: {application.student_ids.map(
                      (studentId) => record.students.find((item) => item.id === studentId)?.name || "Student"
                    ).join(", ") || "Previously recorded application"}</p>
                    {!hosted && <>
                    <p>Offered-award records: {application.awards.length} (fictional, no funds posted)</p>
                    {application.awards.map((award) => (
                      <p key={award.id}>
                        Student award status: {award.decision_status} · Illustrative amount: {
                          new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(award.awarded_cents / 100)
                        }
                      </p>
                    ))}
                    </>}
                  </article>
                ))}
              </section>
              <button type="button" disabled={saving} onClick={refreshStatus}>Refresh saved status</button>
            </>
          ) : null}
        </section>
      </section>
    </CrownDashboardShell>
  );
}

// Both fictional experiences require an explicit build option; backend
// runtime, invitation and guardian checks remain the authorization boundary.
export default function ParentFinancialAidPreparationPage() {
  const local = import.meta.env.VITE_LOCAL_DEMO === "1";
  const hosted = !local && import.meta.env.VITE_HOSTED_JIREH_DEMO === "1";
  return local || hosted ? <FictionalFinancialAidPage hosted={hosted} /> : <ParentJourneyOverviewPage focus="aid" />;
}
