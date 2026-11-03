import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import ParentJourneyOverviewPage from "../features/parentJourney/ParentJourneyOverviewPage.jsx";

const ENDPOINT = "/api/v1/aid/family/demo-intake/";

function errorMessage(error) {
  const data = error?.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  return error instanceof Error ? error.message : "The request could not be completed.";
}

function LocalFictionalFinancialAidPage() {
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

  async function load() {
    const response = await apiFetch(ENDPOINT);
    const data = await response.json();
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
    let active = true;
    apiFetch(ENDPOINT)
      .then((response) => response.json())
      .then((data) => {
        if (!active) return;
        setRecord(data);
        setYearId(data.academic_years[0]?.id || "");
        setScenario(data.scenarios[0]?.id || "");
        setSelectedStudents(data.students.length === 1 ? [data.students[0].id] : []);
        setLoading(false);
      })
      .catch((failure) => {
        if (!active) return;
        setError(errorMessage(failure));
        setLoading(false);
      });
    return () => { active = false; };
  }, []);

  function toggleStudent(studentId) {
    setSelectedStudents((current) =>
      current.includes(studentId)
        ? current.filter((id) => id !== studentId)
        : [...current, studentId]
    );
  }

  const existing = record?.applications?.find(
    (application) => String(application.academic_year_id) === String(yearId)
  );

  async function submit(event) {
    event.preventDefault();
    if (saving || existing) return;
    setError("");
    setConfirmation("");
    setSaving(true);
    try {
      const response = await apiFetch(ENDPOINT, {
        method: "POST",
        body: JSON.stringify({
          academic_year_id: yearId,
          student_ids: selectedStudents,
          household_size: Number(householdSize),
          scenario,
          fictional_acknowledged: acknowledged,
        }),
      });
      const result = await response.json();
      const submitted = result?.application;
      if (result?.demo_only !== true || !submitted?.id) {
        throw new Error("The fictional submission did not return a verifiable application.");
      }

      // A successful POST alone is not proof of persisted or scoped family state.
      // Confirm the canonical application through a separate authenticated GET.
      const refreshed = await load();
      const saved = Array.isArray(refreshed?.applications)
        ? refreshed.applications.find((application) => String(application.id) === String(submitted.id))
        : null;
      const savedStudents = Array.isArray(saved?.student_ids) ? saved.student_ids.map(String) : [];
      const requestedStudents = selectedStudents.map(String);
      if (
        !saved
        || saved.status !== "SUBMITTED"
        || !saved.submitted_at
        || String(saved.academic_year_id) !== String(yearId)
        || savedStudents.length !== requestedStudents.length
        || !requestedStudents.every((id) => savedStudents.includes(id))
      ) {
        throw new Error(
          "The server accepted the fictional submission, but independent saved-record verification failed. Refresh the application status before proceeding."
        );
      }
      setConfirmation("Fictional application #" + saved.id + " submitted and independently verified.");
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <main className="crown-dashboard learning-workflow-page" data-testid="jireh-family-demo">
        <header className="crown-dashboard-hero">
          <div>
            <p className="crown-eyebrow">Jireh Financial Aid · school application</p>
            <h1>Family Financial Aid demonstration</h1>
            <p className="crown-dashboard-purpose">
              Submit a fictional application and review its saved status.
              This isolated local demo is not a real Financial Aid application.
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
                  <select id="jireh-demo-year" value={yearId} onChange={(event) => setYearId(event.target.value)} disabled={saving || Boolean(existing)} required>
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
                    value={householdSize} onChange={(event) => setHouseholdSize(event.target.value)}
                    disabled={Boolean(existing) || saving} required
                  />
                </div>
                <div className="learning-record-detail-block">
                  <label htmlFor="jireh-demo-scenario">Fictional financial scenario</label>
                  <select
                    id="jireh-demo-scenario" value={scenario}
                    onChange={(event) => setScenario(event.target.value)}
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
                      onChange={(event) => setAcknowledged(event.target.checked)}
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
                    disabled={saving || !acknowledged || !yearId || !scenario || selectedStudents.length === 0}
                  >
                    {saving ? "Submitting fictional application…" : "Submit fictional Financial Aid application"}
                  </button>
                )}
              </form>
              <section aria-label="Saved Jireh applications" data-testid="jireh-saved-applications">
                <h2>Saved applications and offered awards</h2>
                {record.applications.length === 0 ? <p>No school Financial Aid applications submitted yet.</p> : null}
                {record.applications.map((application) => (
                  <article key={application.id} className="learning-record-detail-card">
                    <p><strong>Application #{application.id}</strong></p>
                    <p>Year: {application.academic_year_name} · Status: <strong>{application.status}</strong></p>
                    <p>Submitted: {application.submitted_at ? new Date(application.submitted_at).toLocaleString() : "Not submitted"}</p>
                    <p>Selected applicant students: {application.student_ids.map(
                      (studentId) => record.students.find((item) => item.id === studentId)?.name || "Student"
                    ).join(", ") || "Previously recorded application"}</p>
                    <p>Offered-award records: {application.awards.length} (fictional, no funds posted)</p>
                    {application.awards.map((award) => (
                      <p key={award.id}>
                        Student award status: {award.decision_status} · Illustrative amount: {
                          new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(award.awarded_cents / 100)
                        }
                      </p>
                    ))}
                  </article>
                ))}
              </section>
              <button type="button" disabled={saving} onClick={() => {
                setError("");
                setConfirmation("");
                load().catch((failure) => setError(errorMessage(failure)));
              }}>Refresh saved status</button>
            </>
          ) : null}
        </section>
      </main>
    </>
  );
}

// Retain the established production/DEV aid status surface. The fictional
// application form is exclusively a local packaged-demo experience; the
// backend separately enforces its local sandbox and guardian authorization.
export default function ParentFinancialAidPreparationPage() {
  return import.meta.env.VITE_LOCAL_DEMO === "1"
    ? <LocalFictionalFinancialAidPage />
    : <ParentJourneyOverviewPage focus="aid" />;
}
