import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1Section from "./section_assign_wizard/Step1Section.jsx";
import Step2LoadStudents from "./section_assign_wizard/Step2LoadStudents.jsx";
import Step3StageRoster from "./section_assign_wizard/Step3StageRoster.jsx";
import Step4Preview from "./section_assign_wizard/Step4Preview.jsx";
import Step5Commit from "./section_assign_wizard/Step5Commit.jsx";
import Step6Verify from "./section_assign_wizard/Step6Verify.jsx";

const STEP_COMPONENTS = [
  Step1Section,
  Step2LoadStudents,
  Step3StageRoster,
  Step4Preview,
  Step5Commit,
  Step6Verify,
];

const STEP_LABELS = [
  "Section & Term",
  "Load Students",
  "Stage Roster",
  "Preview",
  "Commit",
  "Verify",
];

const STORAGE_KEY = "crown_section_assign_wizard_ctx_v1";

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

export default function SectionAssignWizard() {
  const [initialContext] = useState(() => loadContext());

  function wrappedSetContext(ctx) {
    saveContext(typeof ctx === "function" ? ctx(loadContext()) : ctx);
  }
  void wrappedSetContext;

  return (
    <CrownLayout title="Section Assignments" subtitle="Assign students to a section and commit enrollment records">
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
