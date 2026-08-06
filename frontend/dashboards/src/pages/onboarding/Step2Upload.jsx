import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { createImportSession, uploadImportFile } from "../../api/onboarding.js";
import "../../styles/crown-wizard.css";

export default function Step2Upload({ context, setContext, goBack, goNext, stepIndex, totalSteps, steps }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(context.upload || null);

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      // Create session if we don't have one yet
      let importId = context.importId;
      if (!importId) {
        const sess = await createImportSession(context.mode);
        importId = sess.import_id;
      }
      const upResult = await uploadImportFile(importId, file);
      setResult(upResult);
      setContext((c) => ({ ...c, importId, upload: upResult }));
    } catch (e) {
      setError(e.body?.error || e.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Upload CSV"
        subtitle={`Import mode: ${context.mode}`}
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 14 }}>
        <div style={{ display: "block", fontSize: 13, color: "var(--crown-muted)", marginBottom: 6 }}>
          CSV file (UTF-8, with header row)
        </div>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => { setFile(e.target.files[0] || null); setResult(null); }}
          style={{ color: "var(--crown-text)" }}
        />
      </div>

      {error && <div className="crown-alert" style={{ marginTop: 10 }}>{error}</div>}

      {result && (
        <div className="crown-alert success" style={{ marginTop: 10 }}>
          <strong>Uploaded:</strong> {result.filename} — {result.rows_total} rows
          ({result.students_detected} students, {result.guardians_detected} guardians,
          {result.households_detected} households)
        </div>
      )}

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack}>← Back</button>
        <div className="crown-wizard-actions-right">
          {!result && (
            <button className="crown-btn crown-btn-primary" onClick={handleUpload} disabled={loading || !file}>
              {loading ? "Uploading…" : "Upload"}
            </button>
          )}
          {result && (
            <button className="crown-btn crown-btn-primary" onClick={goNext}>
              Continue →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
