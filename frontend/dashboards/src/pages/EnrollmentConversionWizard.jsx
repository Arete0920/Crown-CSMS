import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1Configure  from "./enrollment_conversion_wizard/Step1Configure.jsx";
import Step2Load       from "./enrollment_conversion_wizard/Step2Load.jsx";
import Step3Preview    from "./enrollment_conversion_wizard/Step3Preview.jsx";
import Step4Commit     from "./enrollment_conversion_wizard/Step4Commit.jsx";
import Step5Verify     from "./enrollment_conversion_wizard/Step5Verify.jsx";

const STEP_COMPONENTS = [Step1Configure, Step2Load, Step3Preview, Step4Commit, Step5Verify];
const STEP_LABELS     = ["Configure", "Load Applicants", "Preview", "Commit", "Verify"];

export default function EnrollmentConversionWizard() {
  const [wizardContext, setWizardContext] = useState({});
  return (
    <CrownLayout title="Enrollment Conversion" subtitle="Convert accepted applicants to enrolled students">
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEP_LABELS}
          initialContext={wizardContext}
          onContextChange={setWizardContext}
        />
      </div>
    </CrownLayout>
  );
}

