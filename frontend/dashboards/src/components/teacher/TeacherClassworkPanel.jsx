import { useCallback, useEffect, useState } from "react";
import { authenticatedFetch } from "../../utils/authClient.js";

async function json(path, options = {}) {
  const response = await authenticatedFetch(path, options);
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

function sectionIdentifier(section) {
  return section?.section_id || section?.id || "";
}

export default function TeacherClassworkPanel() {
  const [sections, setSections] = useState([]);
  const [sectionId, setSectionId] = useState("");
  const [categories, setCategories] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [name, setName] = useState("");
  const [points, setPoints] = useState("10");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    json("/api/v1/academics/sections/?limit=100")
      .then((payload) => {
        const rows = (payload?.results || payload || []).filter((section) => sectionIdentifier(section));
        setSections(rows);
        if (rows.length > 0) setSectionId(String(sectionIdentifier(rows[0])));
      })
      .catch((err) => setError(err?.message || "Unable to load assigned sections."));
  }, []);

  const reloadClasswork = useCallback(async (id) => {
    if (!id) return;
    const [categoryPayload, assignmentPayload] = await Promise.all([
      json(`/api/v1/academics/sections/${encodeURIComponent(id)}/categories/`),
      json(`/api/v1/academics/sections/${encodeURIComponent(id)}/assignments/`),
    ]);
    setCategories(categoryPayload?.categories || []);
    setAssignments(assignmentPayload?.assignments || []);
  }, []);

  useEffect(() => {
    if (!sectionId) return;
    setError("");
    reloadClasswork(sectionId).catch((err) => setError(err?.message || "Unable to load classwork."));
  }, [sectionId, reloadClasswork]);

  async function createAssignment(event) {
    event.preventDefault();
    if (!sectionId || !categories[0]?.id || !name.trim()) return;
    setError("");
    setMessage("");
    try {
      const created = await json(`/api/v1/academics/sections/${encodeURIComponent(sectionId)}/assignments/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          category_id: categories[0].id,
          points_possible: points,
          assigned_date: new Date().toISOString().slice(0, 10),
          is_published: true,
        }),
      });
      setName("");
      await reloadClasswork(sectionId);
      setMessage(`Assignment created and persisted: ${created.name}`);
    } catch (err) {
      setError(err?.message || "Assignment creation failed.");
    }
  }

  return (
    <section aria-label="Teacher classwork transaction" data-testid="teacher-classwork-panel" style={{ marginBottom: 24 }}>
      <h2>Teacher Classwork</h2>
      <p>Create published assignments for your assigned section and reopen them from CROWN.</p>
      {error ? <div role="alert">{error}</div> : null}
      {message ? <div role="status">{message}</div> : null}
      <label>
        Assigned section{" "}
        <select aria-label="Classwork section" value={sectionId} onChange={(event) => setSectionId(event.target.value)}>
          <option value="">-- select --</option>
          {sections.map((section) => {
            const id = String(sectionIdentifier(section));
            return (
              <option key={id} value={id}>
                {section.name || section.course_name || section.title || id}
              </option>
            );
          })}
        </select>
      </label>
      <form onSubmit={createAssignment} style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 12 }}>
        <label>
          Assignment name{" "}
          <input aria-label="Assignment name" value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <label>
          Points possible{" "}
          <input aria-label="Points possible" type="number" min="1" value={points} onChange={(event) => setPoints(event.target.value)} />
        </label>
        <button type="submit" className="crown-btn crown-btn-primary" disabled={!sectionId || !categories.length || !name.trim()}>
          Create assignment
        </button>
      </form>
      <ul aria-label="Published assignments">
        {assignments.map((assignment) => (
          <li key={assignment.id} data-assignment-id={assignment.id}>
            <strong>{assignment.name}</strong> — {assignment.points_possible} points — {assignment.is_published ? "published" : "draft"}
          </li>
        ))}
      </ul>
    </section>
  );
}
