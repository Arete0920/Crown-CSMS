import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1ChooseMode from "./onboarding/Step1ChooseMode.jsx";
import Step2Upload from "./onboarding/Step2Upload.jsx";
import Step3Validate from "./onboarding/Step3Validate.jsx";
import Step4Preview from "./onboarding/Step4Preview.jsx";
import Step5Commit from "./onboarding/Step5Commit.jsx";
import Step6Verify from "./onboarding/Step6Verify.jsx";

const STEP_COMPONENTS = [
  Step1ChooseMode,
  Step2Upload,
  Step3Validate,
  Step4Preview,
  Step5Commit,
  Step6Verify,
];

const STEP_LABELS = [
  "Choose Type",
  "Upload CSV",
  "Validate",
  "Preview",
  "Commit",
  "Verify",
];

const STORAGE_KEY = "crown_onboarding_wizard_ctx_v1";

function loadContext() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : { mode: "students_guardians" };
  } catch {
    return { mode: "students_guardians" };
  }
}

function saveContext(ctx) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ctx));
  } catch { /* ignore */ }
}

export default function AdmissionsIntakeWizard() {
  const [initialContext] = useState(() => loadContext());

  function wrappedSetContext(ctx) {
    saveContext(typeof ctx === "function" ? ctx(loadContext()) : ctx);
  }

  return (
    <CrownLayout title="Student Intake" subtitle="Bulk CSV import wizard">
      {/* Use key to force re-mount on Start New Import (importId cleared) */}
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEP_LABELS}
          initialContext={initialContext}
          // CrownWizard owns setContext; we intercept via wrappedSetContext for persistence
          // Note: because CrownWizard has its own useState, persistence is handled inside steps
        />
      </div>
    </CrownLayout>
  );
}
