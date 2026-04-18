import { useEffect, useState } from "react";
import { fetchCurriculumPacingSummary } from "../api/curriculum.js";
import ErrorBanner from "./ui/ErrorBanner.jsx";

/**
 * CurriculumPacingCard - displays pacing progress for active curriculum courses.
 */
export function CurriculumPacingCard({ schoolId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expandedCourseId, setExpandedCourseId] = useState(null);

  useEffect(() => {
    if (!schoolId) return;

    let alive = true;
    queueMicrotask(() => {
      if (!alive) return;
      setLoading(true);
      setError("");
    });

    fetchCurriculumPacingSummary({ schoolId })
      .then((json) => {
        if (alive) setData(json);
      })
      .catch((e) => {
        if (alive) setError(e?.message || String(e));
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [schoolId]);

  if (!schoolId) {
    return (
      <div style={{ padding: 16, border: "1px solid var(--crown-border)", borderRadius: 4, backgroundColor: "var(--crown-warn-bg)" }}>
        <h3>Curriculum Pacing</h3>
        <p style={{ color: "var(--crown-warn)", fontSize: "0.9em" }}>
          School context missing. Select a school or re-login to see curriculum pacing.
        </p>
      </div>
    );
  }

  const rows = data?.results || [];
  const asOf = rows?.[0]?.pacing?.as_of || null;

  if (error) {
    return <ErrorBanner title="Curriculum Pacing unavailable" message={error} />;
  }

  if (loading) {
    return (
      <div style={{ padding: 16, border: "1px solid var(--crown-border)", borderRadius: 4 }}>
        <h3>Curriculum Pacing</h3>
        <p>Loading...</p>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div style={{ padding: 16, border: "1px solid var(--crown-border)", borderRadius: 4 }}>
        <h3>Curriculum Pacing</h3>
        <p>No active courses found.</p>
      </div>
    );
  }

  const toggleCourse = (courseId) => {
    setExpandedCourseId((current) => (current === courseId ? null : courseId));
  };

  return (
    <div style={{ padding: 16, border: "1px solid var(--crown-border)", borderRadius: 4, backgroundColor: "var(--crown-surface)" }}>
      <h3>Curriculum Pacing</h3>
      <p style={{ fontSize: "0.9em", color: "var(--crown-muted)" }}>
        {asOf ? `As of ${asOf}` : "As of today"} - Click a course to expand units and lessons
      </p>

      <div style={{ marginTop: 12 }}>
        {rows.map((course) => {
          const pct = course?.pacing?.pct_due ?? 0;
          const due = course?.pacing?.due_lessons ?? 0;
          const total = course?.pacing?.total_lessons ?? 0;
          const isExpanded = expandedCourseId === course.course_id;
          const units = course?.units || [];

          return (
            <div key={course.course_id} style={{ marginBottom: 12, borderBottom: "1px solid var(--crown-border)", paddingBottom: 12 }}>
              <button
                type="button"
                onClick={() => toggleCourse(course.course_id)}
                style={{
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "baseline",
                  marginBottom: 4,
                  padding: 8,
                  width: "100%",
                  border: 0,
                  textAlign: "left",
                  backgroundColor: isExpanded ? "var(--crown-surface-2)" : "transparent",
                  borderRadius: 4,
                  transition: "background-color 0.2s",
                }}
                aria-expanded={isExpanded}
              >
                <strong style={{ flex: 1 }}>
                  {isExpanded ? "v" : ">"} {course.code} - {course.name}
                </strong>
                <span style={{ fontSize: "0.9em", color: "var(--crown-muted)" }}>
                  {pct}% ({due}/{total})
                </span>
              </button>

              <div style={{ width: "100%", height: 8, backgroundColor: "var(--crown-border)", borderRadius: 4, overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${pct}%`,
                    backgroundColor: "var(--crown-ok)",
                    transition: "width 0.3s ease",
                  }}
                />
              </div>

              {isExpanded && units.length > 0 && (
                <div style={{ marginTop: 12, marginLeft: 16, paddingLeft: 12, borderLeft: "2px solid var(--crown-border)" }}>
                  {units.map((unit, unitIdx) => {
                    const lessons = unit?.lessons || [];

                    return (
                      <div key={unit.id || unitIdx} style={{ marginBottom: 16 }}>
                        <div style={{ marginBottom: 8 }}>
                          <strong style={{ fontSize: "0.95em", color: "var(--crown-ink)" }}>
                            Unit {unit.order || unitIdx + 1}: {unit.title}
                          </strong>
                          <p style={{ margin: "4px 0", fontSize: "0.85em", color: "var(--crown-muted)", fontStyle: "italic" }}>
                            "{unit.essential_question}"
                          </p>
                          {unit.worldview_focus && (
                            <p style={{ margin: "4px 0", fontSize: "0.8em", color: "var(--crown-muted)" }}>
                              Worldview: {unit.worldview_focus}
                            </p>
                          )}
                        </div>

                        <div style={{ fontSize: "0.85em", color: "var(--crown-muted)" }}>
                          {lessons.length === 0 ? (
                            <p style={{ color: "var(--crown-muted)", fontStyle: "italic" }}>No lessons defined</p>
                          ) : (
                            <ul style={{ margin: "4px 0", paddingLeft: 16 }}>
                              {lessons.map((lesson, lessonIdx) => {
                                const isPast = lesson.planned_date && new Date(lesson.planned_date) <= new Date();
                                return (
                                  <li
                                    key={lesson.id || lessonIdx}
                                    style={{
                                      marginBottom: 4,
                                      color: isPast ? "var(--crown-ok)" : "var(--crown-muted)",
                                      fontWeight: isPast ? "500" : "400",
                                    }}
                                  >
                                    {isPast ? "[x] " : "[ ] "}{lesson.title}
                                    {lesson.planned_date && (
                                      <span style={{ fontSize: "0.75em", color: "var(--crown-muted)", marginLeft: 8 }}>
                                        {new Date(lesson.planned_date).toLocaleDateString("en-US", {
                                          month: "short",
                                          day: "numeric",
                                        })}
                                      </span>
                                    )}
                                  </li>
                                );
                              })}
                            </ul>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
