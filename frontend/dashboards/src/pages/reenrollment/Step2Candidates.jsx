import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { listCandidates } from "../../api/reenrollment.js";
import "../../styles/crown-wizard.css";

export default function Step2Candidates({ context, setContext, goNext, goBack, stepIndex, totalSteps, steps }) {
  const [data, setData] = useState(context.candidates || null);
  const [loading, setLoading] = useState(!context.candidates);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (context.candidates) return;
    (async () => {
      try {
        const result = await listCandidates(context.sessionId);
        setData(result);
        setContext((c) => ({ ...c, candidates: result }));
      } catch (e) {
        setError(e.body?.detail || e.message || "Failed to load candidates.");
      } finally {
        setLoading(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const candidates = data?.candidates || [];

  return (
    <div>
      <CrownWizardStepHeader
        title="Review Eligible Students"
        subtitle={`Active students eligible for re-enrollment into ${context.targetYearLabel || "the new year"}.`}
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      {loading && <p style={{ color: "var(--crown-muted)", marginTop: 16 }}>Loading candidates…</p>}
      {error && <div className="crown-alert" style={{ marginTop: 16 }}>{error}</div>}

      {data && (
        <>
          <div className="crown-card" style={{ padding: "10px 16px", marginTop: 14, display: "flex", gap: 24 }}>
            <span style={{ fontSize: 13 }}>
              <strong style={{ color: "var(--crown-gold)" }}>{data.total}</strong>
              <span style={{ color: "var(--crown-muted)" }}> eligible students</span>
            </span>
            <span style={{ fontSize: 13 }}>
              <strong style={{ color: "var(--crown-text)" }}>${context.enrollmentFee?.toFixed(2)}</strong>
              <span style={{ color: "var(--crown-muted)" }}> per student</span>
            </span>
          </div>

          <div style={{ marginTop: 12, maxHeight: 320, overflowY: "auto", border: "1px solid var(--crown-border)", borderRadius: 6 }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ background: "var(--crown-surface)" }}>
                  <th style={{ textAlign: "left", padding: "8px 12px", color: "var(--crown-muted)", fontWeight: 600 }}>Name</th>
                  <th style={{ textAlign: "left", padding: "8px 12px", color: "var(--crown-muted)", fontWeight: 600 }}>Grade</th>
                </tr>
              </thead>
              <tbody>
                {candidates.slice(0, 200).map((c) => (
                  <tr key={c.id} style={{ borderTop: "1px solid var(--crown-border)" }}>
                    <td style={{ padding: "7px 12px", color: "var(--crown-text)" }}>{c.last_name}, {c.first_name}</td>
                    <td style={{ padding: "7px 12px", color: "var(--crown-muted)" }}>{c.grade_level || "—"}</td>
                  </tr>
                ))}
                {candidates.length > 200 && (
                  <tr>
                    <td colSpan={2} style={{ padding: "8px 12px", color: "var(--crown-muted)", textAlign: "center" }}>
                      … and {candidates.length - 200} more
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack}>← Back</button>
        <div className="crown-wizard-actions-right">
          <button className="crown-btn crown-btn-primary" onClick={goNext} disabled={loading || !!error || !data}>
            Continue →
          </button>
        </div>
      </div>
    </div>
  );
}
