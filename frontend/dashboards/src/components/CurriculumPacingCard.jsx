import { useEffect, useState } from "react";
import { fetchCurriculumPacingSummary } from "../api/curriculum.js";

/**
 * CurriculumPacingCard - displays pacing progress for all active curriculum courses
 * Shows progress bars for each course with % complete based on planned_date <= today
 * Supports click-to-expand to show nested units and lessons (pure UI, no new API calls)
 * 
 * Props:
 *   schoolId (string): required, school UUID for scoping
 */
export function CurriculumPacingCard({ schoolId }) {
  // Guard: ensure schoolId is provided
  if (!schoolId) {
    return (
      <div style={{ padding: 16, border: "1px solid #ddd", borderRadius: 4, backgroundColor: "#fff3cd" }}>
        <h3>Curriculum Pacing</h3>
        <p style={{ color: "#856404", fontSize: "0.9em" }}>
          School context missing. Select a school or re-login to see curriculum pacing.
        </p>
      </div>
    );
  }

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedCourseId, setExpandedCourseId] = useState(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");

    fetchCurriculumPacingSummary({ schoolId })
      .then((json) => alive && setData(json))
      .catch((e) => alive && setError(e?.message || String(e)));

    return () => {
      alive = false;
    };
  }, [schoolId]);

  const rows = (data?.results || []);
  const asOf = rows?.[0]?.pacing?.as_of || null;

  if (error) {
    return (
      <div style={{ padding: 16, border: "1px solid #ccc", borderRadius: 4, backgroundColor: "#fff3cd" }}>
        <h3>Curriculum Pacing</h3>
        <p style={{ color: "#856404" }}>Error: {error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: 16, border: "1px solid #ddd", borderRadius: 4 }}>
        <h3>Curriculum Pacing</h3>
        <p>Loading…</p>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div style={{ padding: 16, border: "1px solid #ddd", borderRadius: 4 }}>
        <h3>Curriculum Pacing</h3>
        <p>No active courses found.</p>
      </div>
    );
  }

  const handleCourseClick = (courseId) => {
    setExpandedCourseId(expandedCourseId === courseId ? null : courseId);
  };

  return (
    <div style={{ padding: 16, border: "1px solid #ddd", borderRadius: 4, backgroundColor: "#fff" }}>
      <h3>Curriculum Pacing</h3>
      <p style={{ fontSize: "0.9em", color: "#666" }}>
        {asOf ? `As of ${asOf}` : "As of today"} • Click course to expand units and lessons
      </p>

      <div style={{ marginTop: 12 }}>
        {rows.map((c) => {
          const pct = c?.pacing?.pct_due ?? 0;
          const due = c?.pacing?.due_lessons ?? 0;
          const total = c?.pacing?.total_lessons ?? 0;
          const isExpanded = expandedCourseId === c.course_id;
          const units = c?.units || [];

          return (
            <div key={c.course_id} style={{ marginBottom: 12, borderBottom: "1px solid #f0f0f0", paddingBottom: 12 }}>
              {/* Course Header (Clickable) */}
              <div 
                onClick={() => handleCourseClick(c.course_id)}
                style={{ 
                  cursor: "pointer",
                  display: "flex", 
                  justifyContent: "space-between", 
                  alignItems: "baseline", 
                  marginBottom: 4,
                  padding: 8,
                  backgroundColor: isExpanded ? "#f5f5f5" : "transparent",
                  borderRadius: 4,
                  transition: "background-color 0.2s"
                }}
              >
                <strong style={{ flex: 1 }}>
                  {isExpanded ? "▼" : "▶"} {c.code} — {c.name}
                </strong>
                <span style={{ fontSize: "0.9em", color: "#666" }}>
                  {pct}% ({due}/{total})
                </span>
              </div>

              {/* Progress Bar */}
              <div style={{ width: "100%", height: 8, backgroundColor: "#e0e0e0", borderRadius: 4, overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${pct}%`,
                    backgroundColor: "#4CAF50",
                    transition: "width 0.3s ease",
                  }}
                />
              </div>

              {/* Expanded Units & Lessons */}
              {isExpanded && units.length > 0 && (
                <div style={{ marginTop: 12, marginLeft: 16, paddingLeft: 12, borderLeft: "2px solid #ddd" }}>
                  {units.map((unit, unitIdx) => {
                    const lessons = unit?.lessons || [];
                    const lessonsWithDate = lessons.filter(l => l.planned_date);
                    const completedLessons = lessonsWithDate.length;

                    return (
                      <div key={unit.id || unitIdx} style={{ marginBottom: 16 }}>
                        {/* Unit Header */}
                        <div style={{ marginBottom: 8 }}>
                          <strong style={{ fontSize: "0.95em", color: "#333" }}>
                            Unit {unit.order || unitIdx + 1}: {unit.title}
                          </strong>
                          <p style={{ margin: "4px 0", fontSize: "0.85em", color: "#666", fontStyle: "italic" }}>
                            "{unit.essential_question}"
                          </p>
                          {unit.worldview_focus && (
                            <p style={{ margin: "4px 0", fontSize: "0.8em", color: "#999" }}>
                              Worldview: {unit.worldview_focus}
                            </p>
                          )}
                        </div>

                        {/* Lessons List */}
                        <div style={{ fontSize: "0.85em", color: "#555" }}>
                          {lessons.length === 0 ? (
                            <p style={{ color: "#999", fontStyle: "italic" }}>No lessons defined</p>
                          ) : (
                            <ul style={{ margin: "4px 0", paddingLeft: 16 }}>
                              {lessons.map((lesson, lessonIdx) => {
                                const isPast = lesson.planned_date && new Date(lesson.planned_date) <= new Date();
                                return (
                                  <li 
                                    key={lesson.id || lessonIdx} 
                                    style={{ 
                                      marginBottom: 4,
                                      color: isPast ? "#4CAF50" : "#999",
                                      fontWeight: isPast ? "500" : "400"
                                    }}
                                  >
                                    {isPast ? "✓ " : "○ "}{lesson.title}
                                    {lesson.planned_date && (
                                      <span style={{ fontSize: "0.75em", color: "#999", marginLeft: 8 }}>
                                        {new Date(lesson.planned_date).toLocaleDateString('en-US', { 
                                          month: 'short', 
                                          day: 'numeric' 
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
