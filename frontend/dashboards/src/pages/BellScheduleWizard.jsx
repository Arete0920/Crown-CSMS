import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1Configure   from "./bell_schedule_wizard/Step1Configure.jsx";
import Step2Periods     from "./bell_schedule_wizard/Step2Periods.jsx";
import Step3Preview     from "./bell_schedule_wizard/Step3Preview.jsx";
import Step4Commit      from "./bell_schedule_wizard/Step4Commit.jsx";
import Step5Verify      from "./bell_schedule_wizard/Step5Verify.jsx";

const STEP_COMPONENTS = [Step1Configure, Step2Periods, Step3Preview, Step4Commit, Step5Verify];
const STEP_LABELS     = ["Label & Year", "Define Periods", "Preview", "Commit", "Verify"];
const STORAGE_KEY     = "crown_bell_schedule_wizard_ctx_v1";

function loadContext() {
  try { const r = sessionStorage.getItem(STORAGE_KEY); return r ? JSON.parse(r) : {}; } catch { return {}; }
}
function saveContext(ctx) {
  try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ctx)); } catch { /* ignore */ }
}

export default function BellScheduleWizard() {
  const [initialContext] = useState(() => loadContext());
  function wrappedSetContext(ctx) {
    saveContext(typeof ctx === "function" ? ctx(loadContext()) : ctx);
  }
  void wrappedSetContext;
  return (
    <CrownLayout title="Bell Schedule" subtitle="Define daily bell schedule periods for a school year">
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
