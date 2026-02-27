import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyReenrollment } from "../../api/reenrollment.js";
import "../../styles/crown-wizard.css";

export default function Step6Verify({ context, setContext, stepIndex, totalSteps, steps }) {
  const [data, setData] = useState(context.verify || null);
  const [loading, setLoading] = useState(!context.verify);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (context.verify) return;
    (async () => {
      try {
        const result = await verifyReenrollment(context.sessionId);
        setData(result);
        setContext((c) => ({ ...c, verify: result }));
      } catch (e) {
        setError(e.body?.detail || e.message || "Verification failed.");
      } finally {
        setLoading(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <CrownWizardStepHeader
        title="Verify Results"
        subtitle="Confirming re-enrollment records were created successfully."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      {loading && <p style={{ color: "var(--crown-muted)", marginTop: 16 }}>Verifying…</p>}
      {error && <div className="crown-alert" style={{ marginTop: 16 }}>{error}</div>}

      {data && (
        <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 10 }}>
          <div className="crown-alert success">
            <strong>Re-enrollment complete</strong> — status: <strong>{data.status}</strong>
          </div>

          <div className="crown-card" style={{ padding: "14px 18px" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <tbody>
                <tr>
                  <td style={{ padding: "5px 0", color: "var(--crown-muted)" }}>Target Year</td>
                  <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 600, color: "var(--crown-text)" }}>
                    {data.target_year_label}
                  </td>
                </tr>
                <tr>
                  <td style={{ padding: "5px 0", color: "var(--crown-muted)" }}>Enrollment Fee</td>
                  <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 600, color: "var(--crown-text)" }}>
                    ${data.enrollment_fee}
                  </td>
                </tr>
                <tr>
                  <td style={{ padding: "5px 0", color: "var(--crown-muted)" }}>Students Re-enrolled</td>
                  <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 700, color: "var(--crown-gold)" }}>
                    {data.students_reenrolled ?? "—"}
                  </td>
                </tr>
                <tr>
                  <td style={{ padding: "5px 0", color: "var(--crown-muted)" }}>Households Invoiced</td>
                  <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 600, color: "var(--crown-text)" }}>
                    {data.households_invoiced ?? "—"}
                  </td>
                </tr>
                <tr style={{ borderTop: "1px solid var(--crown-border)" }}>
                  <td style={{ padding: "8px 0 0", color: "var(--crown-muted)", fontWeight: 600 }}>Total Billed</td>
                  <td style={{ padding: "8px 0 0", textAlign: "right", fontWeight: 700, color: "var(--crown-gold)", fontSize: 15 }}>
                    ${data.total_amount}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p style={{ fontSize: 12, color: "var(--crown-muted)", margin: 0 }}>
            Billing Run ID: <code style={{ fontSize: 11 }}>{data.billing_run_id}</code>
          </p>
        </div>
      )}
    </div>
  );
}
