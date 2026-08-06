import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import { useWizardDraft } from "../hooks/useWizardDraft";
import Step1Mode from "./billing_wizard/Step1Mode.jsx";
import Step2Plans from "./billing_wizard/Step2Plans.jsx";
import Step3Fees from "./billing_wizard/Step3Fees.jsx";
import Step4Schedule from "./billing_wizard/Step4Schedule.jsx";
import Step5Commit from "./billing_wizard/Step5Commit.jsx";
import Step6Verify from "./billing_wizard/Step6Verify.jsx";

const STEP_COMPONENTS = [
  Step1Mode,
  Step2Plans,
  Step3Fees,
  Step4Schedule,
  Step5Commit,
  Step6Verify,
];

const STEP_LABELS = [
  "Mode & Term",
  "Tuition Plans",
  "Fees",
  "Schedule",
  "Commit",
  "Verify",
];

export default function BillingWizard() {
  const [initialContext] = useState(() => ({}));
  const { value, saveDraft, loaded } = useWizardDraft("billing-setup", initialContext);

  if (!loaded) {
    return null;
  }

  return (
    <CrownLayout title="Billing Setup" subtitle="Configure tuition plans, fees, and billing schedule for a term">
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEP_LABELS}
          initialContext={value}
          onContextChange={saveDraft}
        />
      </div>
    </CrownLayout>
  );
}
