import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

function Currency({ value }) {
  const n = parseFloat(value) || 0;
  return <>${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</>;
}

export default function Step4Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const awards = context.awards || [];
  const buckets = context.buckets || [];

  const totalByBucket = buckets.reduce((acc, b) => {
    acc[b] = awards
      .filter((a) => a.bucket === b)
      .reduce((s, a) => s + (parseFloat(a.amount) || 0), 0);
    return acc;
  }, {});

  const grandTotal = awards.reduce((s, a) => s + (parseFloat(a.amount) || 0), 0);

  return (
    <div>
      <CrownWizardStepHeader
        title="Preview"
        subtitle="Review the aid configuration before committing."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Summary card */}
        <div style={{ border: "1px solid var(--crown-border)", borderRadius: 6, padding: "16px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Aid Year</div>
              <div style={{ fontWeight: 600 }}>{context.aidYear || "—"}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Active Buckets</div>
              <div style={{ fontWeight: 600 }}>{buckets.join(", ") || "None"}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Total Awards</div>
              <div style={{ fontWeight: 600 }}>{awards.length}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Total Aid Amount</div>
              <div style={{ fontWeight: 600 }}><Currency value={grandTotal} /></div>
            </div>
          </div>

          {buckets.length > 0 && (
            <>
              <div style={{ fontSize: 12, color: "var(--crown-muted)", marginBottom: 8, fontWeight: 600 }}>
                By Bucket
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--crown-border)" }}>
                    <th style={{ textAlign: "left", padding: "4px 0", fontWeight: 600 }}>Bucket</th>
                    <th style={{ textAlign: "right", padding: "4px 0", fontWeight: 600 }}>Awards</th>
                    <th style={{ textAlign: "right", padding: "4px 0", fontWeight: 600 }}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {buckets.map((b) => (
                    <tr key={b} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                      <td style={{ padding: "6px 0" }}>{b.charAt(0).toUpperCase() + b.slice(1)}</td>
                      <td style={{ padding: "6px 0", textAlign: "right" }}>
                        {awards.filter((a) => a.bucket === b).length}
                      </td>
                      <td style={{ padding: "6px 0", textAlign: "right" }}>
                        <Currency value={totalByBucket[b]} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {awards.length === 0 && (
            <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>
              No awards staged — this cycle will record zero disbursements.
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button className="crown-btn crown-btn--ghost" onClick={goPrev}>Back</button>
          <button className="crown-btn crown-btn--primary" onClick={goNext}>Proceed to Commit</button>
        </div>
      </div>
    </div>
  );
}
