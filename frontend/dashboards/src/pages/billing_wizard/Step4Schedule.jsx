import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

function addDays(dateStr, days) {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function buildSchedule(plan) {
  const rows = [];
  const count = parseInt(plan.installment_count, 10) || 1;
  const cadence = parseInt(plan.cadence_days || 30, 10);
  const amount = parseFloat(plan.total_amount || 0);
  const baseAmt = parseFloat((amount / count).toFixed(2));
  let remainder = parseFloat((amount - baseAmt * (count - 1)).toFixed(2));

  for (let i = 0; i < count; i++) {
    const dueDate = i === 0
      ? plan.first_due_on
      : addDays(plan.first_due_on, cadence * i);
    const rowAmt = i === count - 1 ? remainder : baseAmt;
    rows.push({ seq: i + 1, due_on: dueDate, amount: rowAmt });
  }
  return rows;
}

export default function Step4Schedule({ context, setContext, goNext, goBack, stepIndex, totalSteps, steps }) {
  const plans = context.plans || [];
  const fees = context.fees || [];

  return (
    <div>
      <CrownWizardStepHeader
        title="Schedule Preview"
        subtitle="Review the installment schedule and fee summary before committing."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 20 }}>
        {plans.length === 0 && (
          <div className="crown-alert">No plans configured. Go back and add at least one plan.</div>
        )}

        {plans.map((plan, pi) => {
          const schedule = buildSchedule(plan);
          return (
            <div key={pi} style={{ border: "1px solid var(--crown-border)", borderRadius: 6, overflow: "hidden" }}>
              <div style={{ padding: "10px 14px", background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)", fontWeight: 600, fontSize: 13 }}>
                {plan.name} — ${parseFloat(plan.total_amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2 })} · {plan.installment_count} payment{plan.installment_count !== 1 ? "s" : ""}
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
                    <th style={{ padding: "6px 14px", textAlign: "left" }}>#</th>
                    <th style={{ padding: "6px 14px", textAlign: "left" }}>Due Date</th>
                    <th style={{ padding: "6px 14px", textAlign: "right" }}>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {schedule.map((row) => (
                    <tr key={row.seq} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                      <td style={{ padding: "6px 14px" }}>{row.seq}</td>
                      <td style={{ padding: "6px 14px" }}>{row.due_on}</td>
                      <td style={{ padding: "6px 14px", textAlign: "right" }}>${row.amount.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        })}

        {fees.length > 0 && (
          <div>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Fees ({fees.length})</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, border: "1px solid var(--crown-border)" }}>
              <thead>
                <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
                  <th style={{ padding: "6px 14px", textAlign: "left" }}>Name</th>
                  <th style={{ padding: "6px 14px", textAlign: "left" }}>Type</th>
                  <th style={{ padding: "6px 14px", textAlign: "right" }}>Amount</th>
                  <th style={{ padding: "6px 14px", textAlign: "left" }}>Recurring</th>
                </tr>
              </thead>
              <tbody>
                {fees.map((fee, fi) => (
                  <tr key={fi} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                    <td style={{ padding: "6px 14px" }}>{fee.name}</td>
                    <td style={{ padding: "6px 14px" }}>{fee.fee_type}</td>
                    <td style={{ padding: "6px 14px", textAlign: "right" }}>${parseFloat(fee.amount).toFixed(2)}</td>
                    <td style={{ padding: "6px 14px" }}>{fee.is_recurring ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {fees.length === 0 && <div style={{ fontSize: 12, color: "var(--crown-muted)" }}>No additional fees configured.</div>}
      </div>

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack}>← Back</button>
        <div className="crown-wizard-actions-right">
          <span className="crown-muted" style={{ fontSize: 12 }}>Step {stepIndex + 1} of {totalSteps}</span>
          <button
            className="crown-btn crown-btn-primary"
            onClick={() => { void setContext; goNext(); }}
            disabled={plans.length === 0}
          >
            Looks Good → Commit
          </button>
        </div>
      </div>
    </div>
  );
}
