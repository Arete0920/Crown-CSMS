import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step4Preview({ context, goNext, goBack, stepIndex, totalSteps, steps }) {
  const candidates = context.candidates?.candidates || [];
  const excluded = new Set(context.selectedExcluded || []);
  const selected = candidates.filter((c) => !excluded.has(c.id));
  const fee = context.enrollmentFee ?? 0;
  const totalAmount = (selected.length * fee).toFixed(2);

  // Unique households among selected students
  const householdIds = new Set(selected.map((c) => c.household_id));

  return (
    <div>
      <CrownWizardStepHeader
        title="Preview Re-enrollment"
        subtitle="Review what will be created when you commit. This cannot be undone."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 10 }}>
        <div className="crown-card" style={{ padding: "14px 18px" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <tbody>
              <tr>
                <td style={{ padding: "5px 0", color: "var(--crown-muted)" }}>Target Year</td>
                <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 600, color: "var(--crown-text)" }}>
                  {context.targetYearLabel || "—"}
                </td>
              </tr>
              <tr>
                <td style={{ padding: "5px 0", color: "var(--crown-muted)" }}>Enrollment Fee</td>
                <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 600, color: "var(--crown-text)" }}>
                  ${fee.toFixed(2)} / student
                </td>
              </tr>
              <tr>
                <td style={{ padding: "5px 0", color: "var(--crown-muted)" }}>Students to Re-enroll</td>
                <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 600, color: "var(--crown-gold)" }}>
                  {selected.length}
                </td>
              </tr>
              <tr>
                <td style={{ padding: "5px 0", color: "var(--crown-muted)" }}>Households to Invoice</td>
                <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 600, color: "var(--crown-text)" }}>
                  {householdIds.size}
                </td>
              </tr>
              <tr style={{ borderTop: "1px solid var(--crown-border)" }}>
                <td style={{ padding: "8px 0 0", color: "var(--crown-muted)", fontWeight: 600 }}>Total Billing Amount</td>
                <td style={{ padding: "8px 0 0", textAlign: "right", fontWeight: 700, color: "var(--crown-gold)", fontSize: 15 }}>
                  ${totalAmount}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {excluded.size > 0 && (
          <div className="crown-card" style={{ padding: "10px 16px" }}>
            <span style={{ fontSize: 12, color: "var(--crown-muted)" }}>
              <strong style={{ color: "var(--crown-danger)" }}>{excluded.size}</strong> student{excluded.size !== 1 ? "s" : ""} excluded from this run.
            </span>
          </div>
        )}
      </div>

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack}>← Back</button>
        <div className="crown-wizard-actions-right">
          <button className="crown-btn crown-btn-primary" onClick={goNext}>
            Proceed to Commit →
          </button>
        </div>
      </div>
    </div>
  );
}
