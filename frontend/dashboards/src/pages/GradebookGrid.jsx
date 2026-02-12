import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { authenticatedFetch } from "../utils/authClient";

export default function GradebookGrid() {
  const { sectionId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [pendingUpdates, setPendingUpdates] = useState({});

  const fetchGradebook = () => {
    authenticatedFetch(
      `/api/v1/gradebook/sections/${sectionId}/grades/`
    )
      .then(res => res.json())
      .then(setData)
      .catch(err => {
        console.error("Gradebook fetch failed:", err);
        setError("Failed to load gradebook data.");
      });
  };

  useEffect(() => {
    fetchGradebook();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionId]);

  if (error) return <div style={{ padding: "20px", color: "crimson" }}>{error}</div>;
  if (!data) return <div style={{ padding: "20px" }}>Loading gradebook...</div>;

  const findGradeEntry = (studentId, assignmentName) => {
    const row = data.rows.find(r => r.student.student_id === studentId);
    if (!row) return null;

    return row.scores?.[assignmentName] || null;
  };

  const handleScoreChange = (studentId, assignmentName, value) => {
    setPendingUpdates(prev => ({
      ...prev,
      [`${studentId}_${assignmentName}`]: value
    }));
  };

  const handleScoreSave = async (studentId, assignmentName) => {
    const key = `${studentId}_${assignmentName}`;
    const newValue = pendingUpdates[key];

    if (newValue === undefined) return;

    const entry = findGradeEntry(studentId, assignmentName);
    if (!entry?.grade_entry_id) return;

    try {
      // eslint-disable-next-line no-undef
      await fetch(
        `/api/v1/gradebook/grade-entries/${entry.grade_entry_id}/`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("access")}`,
            "X-School-Id": sessionStorage.getItem("crown.school.id"),
          },
          body: JSON.stringify({
            points_earned: parseFloat(newValue)
          }),
        }
      );

      fetchGradebook();
    } catch (err) {
      console.error("Grade update failed", err);
    }
  };

  // Calculate total possible points across all assignments
  const totalPossible = data.assignments.reduce(
    (sum, a) => sum + (a.points_possible || 0),
    0
  );

  return (
    <div style={{ padding: "20px" }}>
      <div style={{ marginBottom: "20px", paddingBottom: "10px", borderBottom: "1px solid #ccc" }}>
        <h2 style={{ margin: "0 0 8px 0" }}>
          {data.course_name} — {data.term_code}
        </h2>
        <p style={{ margin: 0, color: "#666", fontSize: "14px" }}>
          Section ID: {data.section_id}
        </p>
      </div>

      <div style={{ marginBottom: "15px" }}>
        <button disabled style={{ marginRight: "10px", cursor: "not-allowed", opacity: 0.6 }}>
          Add Assignment
        </button>
        <button disabled style={{ cursor: "not-allowed", opacity: 0.6 }}>
          Export CSV
        </button>
      </div>

      <table border="1" cellPadding="6">
        <thead>
          <tr>
            <th>Student</th>
            {data.assignments.map(a => (
              <th key={a.assignment_name}>
                {a.assignment_name}
              </th>
            ))}
            <th>Percent</th>
          </tr>
        </thead>

        <tbody>
          {data.rows.map(row => {
            // Calculate student's total earned points
            const earned = data.assignments.reduce((sum, a) => {
              const score = row.scores[a.assignment_name];
              return sum + (score && score.points_earned ? score.points_earned : 0);
            }, 0);

            const pct = totalPossible
              ? ((earned / totalPossible) * 100).toFixed(1)
              : "0";

            return (
              <tr key={row.student.student_id}>
                <td>
                  {row.student.first_name}{" "}
                  {row.student.last_name}
                </td>

                {data.assignments.map(a => {
                  const score =
                    row.scores[a.assignment_name];

                  return (
                    <td key={a.assignment_name}>
                      <input
                        type="number"
                        step="0.01"
                        value={
                          pendingUpdates[`${row.student.student_id}_${a.assignment_name}`] !== undefined
                            ? pendingUpdates[`${row.student.student_id}_${a.assignment_name}`]
                            : score
                            ? score.points_earned
                            : ""
                        }
                        onChange={(e) =>
                          handleScoreChange(
                            row.student.student_id,
                            a.assignment_name,
                            e.target.value
                          )
                        }
                        onBlur={() =>
                          handleScoreSave(
                            row.student.student_id,
                            a.assignment_name
                          )
                        }
                      />
                    </td>
                  );
                })}

                <td>
                  <strong>{pct}%</strong>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
