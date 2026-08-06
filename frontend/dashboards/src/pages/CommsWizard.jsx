import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1Purpose from "./comms_wizard/Step1Purpose.jsx";
import Step2Message from "./comms_wizard/Step2Message.jsx";
import Step3Recipients from "./comms_wizard/Step3Recipients.jsx";
import Step4Preview from "./comms_wizard/Step4Preview.jsx";
import Step5Commit from "./comms_wizard/Step5Commit.jsx";
import Step6Verify from "./comms_wizard/Step6Verify.jsx";

const STEP_COMPONENTS = [
  Step1Purpose,
  Step2Message,
  Step3Recipients,
  Step4Preview,
  Step5Commit,
  Step6Verify,
];

const STEP_LABELS = [
  "Purpose & Channels",
  "Message",
  "Recipients",
  "Preview",
  "Commit",
  "Verify",
];

const STORAGE_KEY = "crown_comms_wizard_ctx_v1";

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

export default function CommsWizard() {
  const [initialContext] = useState(() => loadContext());

  function wrappedSetContext(ctx) {
    saveContext(typeof ctx === "function" ? ctx(loadContext()) : ctx);
  }
  void wrappedSetContext;

  return (
    <CrownLayout title="Communications Setup" subtitle="Configure and queue a communication campaign">
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
