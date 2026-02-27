import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1Year from "./financial_aid_wizard/Step1Year.jsx";
import Step2Buckets from "./financial_aid_wizard/Step2Buckets.jsx";
import Step3Awards from "./financial_aid_wizard/Step3Awards.jsx";
import Step4Preview from "./financial_aid_wizard/Step4Preview.jsx";
import Step5Commit from "./financial_aid_wizard/Step5Commit.jsx";
import Step6Verify from "./financial_aid_wizard/Step6Verify.jsx";

const STEP_COMPONENTS = [
  Step1Year,
  Step2Buckets,
  Step3Awards,
  Step4Preview,
  Step5Commit,
  Step6Verify,
];

const STEP_LABELS = [
  "Aid Year",
  "Buckets",
  "Awards",
  "Preview",
  "Commit",
  "Verify",
];

const STORAGE_KEY = "crown_aid_wizard_ctx_v1";

function loadContext() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveContext(ctx) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ctx));
  } catch { /* ignore */ }
}

export default function FinancialAidWizard() {
  const [initialContext] = useState(() => loadContext());

  function wrappedSetContext(ctx) {
    saveContext(typeof ctx === "function" ? ctx(loadContext()) : ctx);
  }
  void wrappedSetContext;

  return (
    <CrownLayout title="Financial Aid Setup" subtitle="Configure aid year, active buckets, and create awards for the aid cycle">
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEP_LABELS}
          initialContext={initialContext}
        />
      </div>
    </CrownLayout>
  );
}
