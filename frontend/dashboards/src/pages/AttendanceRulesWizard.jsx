import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import Step1Configure  from "./attendance_rules_wizard/Step1Configure.jsx";
import Step2Codes      from "./attendance_rules_wizard/Step2Codes.jsx";
import Step3Preview    from "./attendance_rules_wizard/Step3Preview.jsx";
import Step4Commit     from "./attendance_rules_wizard/Step4Commit.jsx";
import Step5Verify     from "./attendance_rules_wizard/Step5Verify.jsx";

const STEP_COMPONENTS = [Step1Configure, Step2Codes, Step3Preview, Step4Commit, Step5Verify];
const STEP_LABELS     = ["Label & Year", "Define Codes", "Preview", "Commit", "Verify"];

export default function AttendanceRulesWizard() {
  return (
    <CrownLayout title="Attendance Rules" subtitle="Define attendance codes and rules for a school year">
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEP_LABELS}
        />
      </div>
    </CrownLayout>
  );
}

