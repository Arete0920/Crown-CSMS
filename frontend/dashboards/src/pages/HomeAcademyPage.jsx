import { useCallback, useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { activateHomeAcademyRegistration, completeHomeAcademyRegistration, fetchHomeAcademyBoardSummary, fetchHomeAcademyConfig, fetchHomeAcademyOfferings, fetchHomeAcademyRegistrations, postHomeAcademyTranscript } from "../api/homeAcademyApi.js";

const TH = { padding: "8px 10px", textAlign: "left", borderBottom: "2px solid var(--crown-border)" };
const TD = { padding: "8px 10px", borderBottom: "1px solid var(--crown-border)", verticalAlign: "top" };
const BTN = { marginRight: 8, marginBottom: 4 };

export default function HomeAcademyPage() {
  const [state, setState] = useState({ program: null, summary: null, offerings: [], registrations: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [grades, setGrades] = useState({});

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [program, summary, offerings, registrations] = await Promise.all([
        fetchHomeAcademyConfig(), fetchHomeAcademyBoardSummary(),
        fetchHomeAcademyOfferings(), fetchHomeAcademyRegistrations(),
      ]);
      setState({ program, summary, offerings, registrations });
    } catch (err) { setError(err.message || "Unable to load Home Academy."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function run(action) {
    setError("");
    try { await action(); await load(); }
    catch (err) { setError(err.message || "Home Academy action failed."); }
  }

  return (
    <CrownLayout title="Home Academy">
      <DashboardSection title={state.program?.public_program_name || "Home Academy Operations"}>
        {loading && <p>Loading Home Academy...</p>}
        {error && <div role="alert" style={{ color: "var(--crown-danger)", marginBottom: 12 }}>{error}</div>}
        {!loading && state.summary && (
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 16 }}>
            <strong>Active students: {state.summary.active_enrollments}</strong>
            <strong>Active offerings: {state.summary.active_offerings}</strong>
            <strong>Pending registrations: {state.summary.pending_registrations}</strong>
          </div>
        )}
      </DashboardSection>
      <DashboardSection title="Offerings">
        <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr><th style={TH}>Offering</th><th style={TH}>Type</th><th style={TH}>Term</th><th style={TH}>Price</th><th style={TH}>Credit</th><th style={TH}>Seats</th></tr></thead>
          <tbody>
            {state.offerings.map((row) => <tr key={row.id}>
              <td style={TD}>{row.title}</td><td style={TD}>{row.offering_type}</td>
              <td style={TD}>{row.school_year} {row.term}</td><td style={TD}>{"$"}{row.price}</td>
              <td style={TD}>{row.credit_bearing ? "Yes" : "No"}</td><td style={TD}>{row.homeschool_seat_cap}</td>
            </tr>)}
            {!loading && state.offerings.length === 0 && <tr><td style={TD} colSpan={6}>No active offerings.</td></tr>}
          </tbody>
        </table></div>
      </DashboardSection>
      <DashboardSection title="Registrations">
        <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr><th style={TH}>Student</th><th style={TH}>Offering</th><th style={TH}>Status</th><th style={TH}>Eligibility</th><th style={TH}>Aid</th><th style={TH}>Transcript</th><th style={TH}>Actions</th></tr></thead>
          <tbody>
            {state.registrations.map((row) => <tr key={row.id}>
              <td style={TD}>{row.student_id}</td><td style={TD}>{state.offerings.find((o) => o.id === row.offering)?.title || row.offering}</td>
              <td style={TD}>{row.status}</td><td style={TD}>{row.eligibility_status}</td>
              <td style={TD}>{row.aid_eligible ? "Eligible" : "Not eligible"}</td><td style={TD}>{row.transcript_posting_status}</td>
              <td style={TD}>
                {["eligible", "pending_eligibility", "waitlisted", "approved"].includes(row.status) && <button type="button" style={BTN} onClick={() => run(() => activateHomeAcademyRegistration(row.id))}>Activate</button>}
                {row.status === "active" && <>
                  <input aria-label={"Letter grade for registration " + row.id} placeholder="Grade" maxLength={2} value={grades[row.id]?.letter || ""} onChange={(e) => setGrades((g) => ({ ...g, [row.id]: { ...g[row.id], letter: e.target.value } }))} style={{ width: 58, marginRight: 4 }} />
                  <input aria-label={"Percentage for registration " + row.id} placeholder="%" type="number" min="0" max="100" step="0.01" value={grades[row.id]?.percentage || ""} onChange={(e) => setGrades((g) => ({ ...g, [row.id]: { ...g[row.id], percentage: e.target.value } }))} style={{ width: 72, marginRight: 4 }} />
                  <button type="button" style={BTN} onClick={() => run(() => completeHomeAcademyRegistration(row.id, { final_letter_grade: grades[row.id]?.letter || "", final_percentage: grades[row.id]?.percentage || null }))}>Complete</button>
                </>}
                {row.transcript_posting_status === "pending_registrar" && <button type="button" style={BTN} onClick={() => run(() => postHomeAcademyTranscript(row.id))}>Post transcript</button>}
              </td>
            </tr>)}
            {!loading && state.registrations.length === 0 && <tr><td style={TD} colSpan={7}>No registrations.</td></tr>}
          </tbody>
        </table></div>
      </DashboardSection>
    </CrownLayout>
  );
}
