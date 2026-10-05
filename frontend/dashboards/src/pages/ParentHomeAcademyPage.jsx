import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { fetchParentHomeAcademySummary } from "../api/homeAcademyApi.js";

const TH = { padding: "8px 10px", textAlign: "left", borderBottom: "2px solid var(--crown-border)" };
const TD = { padding: "8px 10px", borderBottom: "1px solid var(--crown-border)", verticalAlign: "top" };

export default function ParentHomeAcademyPage() {
  const [data, setData] = useState({ program: null, students: [], offerings: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchParentHomeAcademySummary()
      .then((payload) => { if (!cancelled) setData(payload); })
      .catch((err) => { if (!cancelled) setError(err.message || "Unable to load Home Academy."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <CrownLayout title={data.program?.public_program_name || "Home Academy"}>
      <DashboardSection title="My Family">
        {loading && <p>Loading Home Academy...</p>}
        {error && <div role="alert" style={{ color: "var(--crown-danger)" }}>{error}</div>}
        {!loading && data.students.map((student) => (
          <div key={student.id} style={{ marginBottom: 16 }}>
            <h3>{student.name}</h3>
            <p>
              Affiliation: {student.home_academy_enrollment?.status || "Not enrolled"}
              {student.home_academy_enrollment?.school_of_record_status ? " · School of record: " + student.home_academy_enrollment.school_of_record_status : ""}
            </p>
            {student.registrations.length > 0 && <ul>
              {student.registrations.map((registration) => <li key={registration.id}>
                {data.offerings.find((o) => o.id === registration.offering)?.title || "Offering"} — {registration.status}
              </li>)}
            </ul>}
          </div>
        ))}
        {!loading && data.students.length === 0 && <p>No active students are linked to this parent account.</p>}
      </DashboardSection>
      <DashboardSection title="Available Offerings">
        <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr><th style={TH}>Offering</th><th style={TH}>Type</th><th style={TH}>Term</th><th style={TH}>Price</th><th style={TH}>Credit</th></tr></thead>
          <tbody>
            {data.offerings.map((row) => <tr key={row.id}>
              <td style={TD}>{row.title}</td><td style={TD}>{row.offering_type}</td>
              <td style={TD}>{row.school_year} {row.term}</td><td style={TD}>{"$"}{row.price}</td>
              <td style={TD}>{row.credit_bearing ? "Yes" : "No"}</td>
            </tr>)}
            {!loading && data.offerings.length === 0 && <tr><td style={TD} colSpan={5}>No offerings are currently available.</td></tr>}
          </tbody>
        </table></div>
      </DashboardSection>
    </CrownLayout>
  );
}
