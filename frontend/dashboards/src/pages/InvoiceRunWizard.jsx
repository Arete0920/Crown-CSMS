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

export default function InvoiceRunWizard() {
  const [context, setContext] = useState({});
  return (
    <CrownLayout title="Invoice Run" subtitle="Generate invoices from open billing obligations">
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEP_LABELS}
          initialContext={context}
          onContextChange={setContext}
        />
      </div>
    </CrownLayout>
  );
}
