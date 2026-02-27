import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1Config from "./reenrollment/Step1Config.jsx";
import Step2Candidates from "./reenrollment/Step2Candidates.jsx";
import Step3Select from "./reenrollment/Step3Select.jsx";
import Step4Preview from "./reenrollment/Step4Preview.jsx";
import Step5Commit from "./reenrollment/Step5Commit.jsx";
import Step6Verify from "./reenrollment/Step6Verify.jsx";

const STEP_COMPONENTS = [
  Step1Config,
  Step2Candidates,
  Step3Select,
  Step4Preview,
  Step5Commit,
  Step6Verify,
];

const STEP_LABELS = [
  "Configure",
  "Candidates",
  "Select",
  "Preview",
  "Commit",
  "Verify",
];

const STORAGE_KEY = "crown_reenrollment_wizard_ctx_v1";

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

export default function ReenrollmentWizard() {
  const [initialContext] = useState(() => loadContext());

  function wrappedSetContext(ctx) {
    saveContext(typeof ctx === "function" ? ctx(loadContext()) : ctx);
  }
  void wrappedSetContext; // referenced for side-effect safety; CrownWizard owns setContext

  return (
    <CrownLayout title="Re-enrollment" subtitle="Re-enroll active students and generate enrollment-fee invoices">
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
