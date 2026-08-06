/**
 * SetupProgress.jsx
 */
import { useEffect, useState } from "react";
import { apiFetch } from "../utils/apiFetch";

export default function SetupProgress({ schoolId }) {
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(Boolean(schoolId));
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!schoolId) return;
    apiFetch(`/api/v1/onboarding/${schoolId}/progress/`)
      .then((res) => res.json())
      .then((data) => {
        setProgress(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [schoolId]);

  if (loading) return <div aria-busy="true">Loading setup progress...</div>;
  if (error) return <div role="alert">Failed to load setup progress: {error}</div>;
  if (!progress) return null;

  const pct = progress.percent_complete ?? 0;

  return (
    <div className="progress-card" aria-label="School setup progress">
      <h3>Setup Progress</h3>
      <p aria-label={`${pct} percent complete`}>
        <strong>{pct}%</strong> Complete ({progress.completed} / {progress.total_tasks} tasks)
      </p>
      <progress value={pct} max={100} aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} />
      <ul aria-label="Onboarding task list">
        {(progress.tasks ?? []).map((task) => (
          <li key={task.id} aria-label={`${task.task_name}: ${task.status}`}>
            <span>{task.status === "complete" ? "[x]" : "[ ]"}</span>{" "}
            {task.task_name}
          </li>
        ))}
      </ul>
    </div>
  );
}
