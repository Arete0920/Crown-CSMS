import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1Configure  from "./invoice_run_wizard/Step1Configure.jsx";
import Step2Load       from "./invoice_run_wizard/Step2Load.jsx";
import Step3Preview    from "./invoice_run_wizard/Step3Preview.jsx";
import Step4Commit     from "./invoice_run_wizard/Step4Commit.jsx";
import Step5Verify     from "./invoice_run_wizard/Step5Verify.jsx";

const STEP_COMPONENTS = [Step1Configure, Step2Load, Step3Preview, Step4Commit, Step5Verify];
const STEP_LABELS     = ["Configure Period", "Load Obligations", "Preview", "Commit", "Verify"];
const STORAGE_KEY     = "crown_invoice_run_wizard_ctx_v1";

function loadContext() {
  try { const r = sessionStorage.getItem(STORAGE_KEY); return r ? JSON.parse(r) : {}; } catch { return {}; }
}
function saveContext(ctx) {
  try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ctx)); } catch { /* ignore */ }
}

export default function InvoiceRunWizard() {
  const [initialContext] = useState(() => loadContext());
  function wrappedSetContext(ctx) {
    saveContext(typeof ctx === "function" ? ctx(loadContext()) : ctx);
  }
  void wrappedSetContext;
  return (
    <CrownLayout title="Invoice Run" subtitle="Generate invoices from open billing obligations">
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEP_LABELS}
          initialContext={initialContext}
          onContextChange={saveContext}
          onComplete={() => { sessionStorage.removeItem(STORAGE_KEY); }}
        />
      </div>
    </CrownLayout>
  );
}
