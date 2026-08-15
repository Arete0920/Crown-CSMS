import { useEffect, useMemo, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import {
  configureSchedulingSession,
  createSchedulingWizardSession,
  getSchedulingScopeOptions,
} from "../../api/scheduling_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step1Term({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [academicYearId, setAcademicYearId] = useState(context.academicYearId || "");
  const [termId, setTermId] = useState(context.termId || "");
  const [scope, setScope] = useState({ academic_years: [], terms: [] });
  const [loading, setLoading] = useState(false);
  const [loadingScope, setLoadingScope] = useState(true);
  const [error, setError] = useState(null);

  const academicYears = Array.isArray(scope?.academic_years) ? scope.academic_years : [];
  const terms = Array.isArray(scope?.terms) ? scope.terms : [];

  useEffect(() => {
    let active = true;
    async function loadScope() {
      setLoadingScope(true);
      setError(null);
      try {
        const data = await getSchedulingScopeOptions();
        if (!active) return;
        const normalizedScope = {
          ...data,
          academic_years: Array.isArray(data?.academic_years) ? data.academic_years : [],
          terms: Array.isArray(data?.terms) ? data.terms : [],
        };
        setScope(normalizedScope);
        const preferredYear = academicYearId
          || normalizedScope.academic_years.find((year) => year.is_current)?.academic_year_id
          || normalizedScope.academic_years[0]?.academic_year_id
          || "";
        setAcademicYearId(preferredYear);
        if (!termId && preferredYear) {
          const preferredTerm = normalizedScope.terms.find(
            (term) => term.academic_year_id === preferredYear && term.active,
          ) || normalizedScope.terms.find((term) => term.academic_year_id === preferredYear);
          setTermId(preferredTerm?.term_id || "");
        }
      } catch (e) {
        if (active) setError(e.body?.error || e.message || "Unable to load canonical scheduling scope.");
      } finally {
        if (active) setLoadingScope(false);
      }
    }
    loadScope();
    return () => { active = false; };
  }, []);

  const availableTerms = useMemo(
    () => terms.filter((term) => term.academic_year_id === academicYearId),
    [terms, academicYearId],
  );

  function handleYearChange(value) {
    setAcademicYearId(value);
    const nextTerm = terms.find(
      (term) => term.academic_year_id === value && term.active,
    ) || terms.find((term) => term.academic_year_id === value);
    setTermId(nextTerm?.term_id || "");
  }

  async function handleContinue() {
    if (!academicYearId) { setError("Select an academic year."); return; }
    if (!termId) { setError("Select a canonical term."); return; }

    setLoading(true);
    setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createSchedulingWizardSession();
        sessionId = created.session_id;
      }
      const data = await configureSchedulingSession(sessionId, academicYearId, termId);
      const selectedYear = academicYears.find((year) => year.academic_year_id === academicYearId);
      const selectedTerm = terms.find((term) => term.term_id === termId);
      setContext({
        sessionId,
        academicYearId,
        termId,
        schoolYear: selectedYear?.name || "",
        term: selectedTerm?.code || "",
        configure: data,
        courses: null,
        sections: null,
        commit: null,
        verify: null,
      });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Configuration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Scheduling Scope"
        subtitle="Select the canonical academic year and term for this scheduling run."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <div style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Academic Year *
          </div>
          <select
            className="crown-input"
            value={academicYearId}
            onChange={(e) => handleYearChange(e.target.value)}
            disabled={loadingScope}
            style={{ width: "100%", boxSizing: "border-box" }}
          >
            <option value="">Select academic year</option>
            {academicYears.map((year) => (
              <option key={year.academic_year_id} value={year.academic_year_id}>
                {year.name}{year.is_current ? " — Current" : ""}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Term *
          </div>
          <select
            className="crown-input"
            value={termId}
            onChange={(e) => setTermId(e.target.value)}
            disabled={loadingScope || !academicYearId}
            style={{ width: "100%", boxSizing: "border-box" }}
          >
            <option value="">Select term</option>
            {availableTerms.map((term) => (
              <option key={term.term_id} value={term.term_id}>
                {term.code} — {term.name}{term.active ? "" : " — Inactive"}
              </option>
            ))}
          </select>
          <span style={{ fontSize: 11, color: "var(--crown-muted)" }}>
            Terms are loaded from the canonical academic calendar; free-text scheduling scope is disabled.
          </span>
        </div>

        {error && <div className="crown-alert">{error}</div>}

        <button
          className="crown-btn crown-btn-primary"
          onClick={handleContinue}
          disabled={loading || loadingScope || !academicYearId || !termId}
          style={{ alignSelf: "flex-start" }}
        >
          {loading ? "Saving…" : "Continue →"}
        </button>
      </div>
    </div>
  );
}