/**
 * BoardTrends.jsx
 *
 * Board KPI trend chart (tabular for now; wire to recharts if desired).
 * Fetches /api/v1/board/trends/ and renders monthly revenue + enrollment.
 *
 * Props:
 *   schoolId (string) — injected via X-School-Id header by apiFetch
 */
import { useEffect, useState } from "react";
import { apiFetch } from "../utils/apiFetch";

export default function BoardTrends() {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiFetch("/api/v1/board/trends/")
      .then((res) => res.json())
      .then((data) => {
        setTrends(data.trends ?? []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div aria-busy="true">Loading board trends…</div>;
  if (error) return <div role="alert">Failed to load trends: {error}</div>;

  return (
    <section aria-label="Board KPI Trends">
      <h3>Board KPI Trends</h3>
      {trends.length === 0 ? (
        <p>No trend data yet. KPI snapshots will appear here once recorded.</p>
      ) : (
        <table aria-label="Monthly KPI trend table" style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th scope="col">Month</th>
              <th scope="col">Revenue</th>
              <th scope="col">Enrollment</th>
              <th scope="col">Discipline Incidents</th>
            </tr>
          </thead>
          <tbody>
            {trends.map((row, i) => (
              <tr key={i}>
                <td>{row.month}</td>
                <td aria-label={`Revenue $${row.revenue}`}>${Number(row.revenue).toLocaleString()}</td>
                <td>{row.enrollment}</td>
                <td>{row.discipline_incidents}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
