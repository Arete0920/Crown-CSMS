import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import { useWizardDraft } from "../hooks/useWizardDraft";
import Step1Term from "./scheduling_wizard/Step1Term.jsx";
import Step2Courses from "./scheduling_wizard/Step2Courses.jsx";
import Step3Sections from "./scheduling_wizard/Step3Sections.jsx";
import Step4Preview from "./scheduling_wizard/Step4Preview.jsx";
import Step5Commit from "./scheduling_wizard/Step5Commit.jsx";
import Step6Verify from "./scheduling_wizard/Step6Verify.jsx";

const STEP_COMPONENTS = [
  Step1Term,
  Step2Courses,
  Step3Sections,
  Step4Preview,
  Step5Commit,
  Step6Verify,
];

const STEP_LABELS = [
  "Term Setup",
  "Courses",
  "Sections",
  "Preview",
  "Commit",
  "Verify",
];

export default function SchedulingWizard() {
  const [initialContext] = useState(() => ({}));
  const { value, saveDraft, loaded } = useWizardDraft("scheduling-setup", initialContext);

  if (!loaded) {
    return null;
  }

  return (
    <CrownLayout title="Scheduling Setup" subtitle="Define courses and sections for a term">
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
