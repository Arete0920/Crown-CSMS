import { useEffect, useMemo, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner";
import EmptyState from "../components/ui/EmptyState";
import { authenticatedFetch } from "../utils/authClient.js";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const PERSISTED_FIELDS = ["objectives", "materials", "activities", "homework", "teacher_notes_private"];

async function requestJson(path, options = {}) {
  const response = await authenticatedFetch(`${API_BASE}${path}`, options);
  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }
  if (!response.ok) {
    const detail = payload?.detail || payload?.message || text || `HTTP ${response.status}`;
    throw new Error(String(detail));
  }
  return payload;
}

function normalizeSections(payload) {
  return payload?.results || payload?.items || payload || [];
}

function firstPlan(payload) {
  if (Array.isArray(payload)) return payload[0] || null;
  return payload?.results?.[0] || payload?.items?.[0] || null;
}

function blankPlan(planDate) {
  return {
    plan_date: planDate,
    objectives: "",
    materials: "",
    activities: "",
    homework: "",
    teacher_notes_private: "",
    lesson_ids: [],
  };
}

function persistedPlanMatches(expected, actual) {
  if (!actual) return false;
  if (String(actual.plan_date || "") !== String(expected.plan_date || "")) return false;
  return PERSISTED_FIELDS.every((field) => String(actual[field] || "") === String(expected[field] || ""));
}

export default function TeacherLessonPlanPage() {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const [sections, setSections] = useState([]);
  const [sectionId, setSectionId] = useState("");
  const [planDate, setPlanDate] = useState(today);
  const [plan, setPlan] = useState(blankPlan(today));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const payload = await requestJson("/api/v1/academics/sections/?limit=100");
        if (!active) return;
        const available = normalizeSections(payload);
        setSections(available);
        if (available.length > 0) setSectionId(String(available[0].id));
      } catch (err) {
        if (active) setError(err.message || "Unable to load assigned sections.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!sectionId || !planDate) return;
    let active = true;
    (async () => {
      setLoading(true);
      setError("");
      setMessage("");
      try {
        const payload = await requestJson(
          `/api/v1/academics/sections/${encodeURIComponent(sectionId)}/lesson-plans/?date=${encodeURIComponent(planDate)}`
        );
        if (!active) return;
        const existing = firstPlan(payload);
        setPlan(existing ? { ...blankPlan(planDate), ...existing } : blankPlan(planDate));
        setMessage(existing ? "Saved lesson plan reopened from CROWN." : "No saved plan exists for this section and date yet.");
      } catch (err) {
        if (active) setError(err.message || "Unable to load the lesson plan.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [sectionId, planDate]);

  function updateField(field, value) {
    setPlan((current) => ({ ...current, [field]: value }));
  }

  async function savePlan(event) {
    event.preventDefault();
    if (!sectionId) return;
    setSaving(true);
    setError("");
    setMessage("Saving lesson plan to CROWN...");
    const expected = {
      plan_date: planDate,
      lesson_ids: Array.isArray(plan.lesson_ids) ? plan.lesson_ids : [],
      objectives: plan.objectives || "",
      materials: plan.materials || "",
      activities: plan.activities || "",
      homework: plan.homework || "",
      teacher_notes_private: plan.teacher_notes_private || "",
    };
    try {
      await requestJson(
        `/api/v1/academics/sections/${encodeURIComponent(sectionId)}/lesson-plans/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(expected),
        }
      );

      const reloadedPayload = await requestJson(
        `/api/v1/academics/sections/${encodeURIComponent(sectionId)}/lesson-plans/?date=${encodeURIComponent(planDate)}`
      );
      const persisted = firstPlan(reloadedPayload);
      if (!persistedPlanMatches(expected, persisted)) {
        throw new Error("The save request completed, but the persisted lesson plan did not match the submitted values after reload.");
      }

      setPlan({ ...blankPlan(planDate), ...persisted });
      setMessage("Lesson plan saved, reopened, and persistence verified in CROWN.");
    } catch (err) {
      setError(err.message || "Lesson plan save failed.");
      setMessage("");
    } finally {
      setSaving(false);
    }
  }

  return (
    <CrownLayout
      title="Teacher Lesson Plans"
      subtitle="Create, save, reopen, and update instructional plans for assigned sections"
      mainClassName="crown-teacher-lesson-plan"
    >
      <main data-testid="teacher-lesson-plan-editor">
        <header className="crown-dashboard-hero">
          <div>
            <p className="crown-eyebrow">Teacher workflow</p>
            <h1>Lesson Plan Editor</h1>
            <p className="crown-dashboard-purpose">
              Build the instructional plan for the selected class and date. Every successful save is immediately reloaded from CROWN and compared with the submitted values before success is shown.
            </p>
          </div>
        </header>

        {error && <ErrorBanner title="Lesson plan error" message={error} />}
        {message && <div role="status" aria-live="polite" className="sandbox-message is-info">{message}</div>}

        {!loading && sections.length === 0 ? (
          <EmptyState
            title="No assigned sections"
            message="This teacher account needs at least one authorized section before lesson plans can be created."
          />
        ) : (
          <form onSubmit={savePlan} aria-label="Teacher lesson plan editor">
            <div className="crown-filter-row" style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 16 }}>
              <label>
                <strong>Section</strong><br />
                <select
                  aria-label="Lesson plan section"
                  value={sectionId}
                  onChange={(event) => setSectionId(event.target.value)}
                  disabled={loading || saving}
                >
                  <option value="">-- select --</option>
                  {sections.map((section) => (
                    <option key={section.id} value={section.id}>
                      {section.name || section.course_name || section.title || section.id}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <strong>Plan date</strong><br />
                <input
                  aria-label="Lesson plan date"
                  type="date"
                  value={planDate}
                  onChange={(event) => setPlanDate(event.target.value)}
                  disabled={saving}
                />
              </label>
            </div>

            <div style={{ display: "grid", gap: 16 }}>
              <label>
                <strong>Learning objectives</strong><br />
                <textarea aria-label="Learning objectives" rows="4" value={plan.objectives || ""} onChange={(e) => updateField("objectives", e.target.value)} />
              </label>
              <label>
                <strong>Materials and curriculum resources</strong><br />
                <textarea aria-label="Materials and curriculum resources" rows="4" value={plan.materials || ""} onChange={(e) => updateField("materials", e.target.value)} placeholder="Textbook pages, curriculum unit, links, files, or classroom materials" />
              </label>
              <label>
                <strong>Instructional activities</strong><br />
                <textarea aria-label="Instructional activities" rows="6" value={plan.activities || ""} onChange={(e) => updateField("activities", e.target.value)} />
              </label>
              <label>
                <strong>Homework / follow-up</strong><br />
                <textarea aria-label="Homework" rows="3" value={plan.homework || ""} onChange={(e) => updateField("homework", e.target.value)} />
              </label>
              <label>
                <strong>Private teacher notes</strong><br />
                <textarea aria-label="Private teacher notes" rows="3" value={plan.teacher_notes_private || ""} onChange={(e) => updateField("teacher_notes_private", e.target.value)} />
              </label>
            </div>

            <div style={{ marginTop: 18 }}>
              <button className="crown-btn crown-btn-primary" type="submit" disabled={!sectionId || loading || saving}>
                {saving ? "Saving and verifying..." : "Save lesson plan"}
              </button>
            </div>
          </form>
        )}
      </main>
    </CrownLayout>
  );
}
