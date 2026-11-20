import { useEffect, useState } from "react";
import { clearFinancialAidWizardDrafts, getAccessToken, getSelectedSchoolId, SCHOOL_CONTEXT_CHANGE_EVENT, AUTH_CONTEXT_CHANGE_EVENT } from "../utils/authClient.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownWizard from "../components/crown/CrownWizard.jsx";
import { useWizardDraft } from "../hooks/useWizardDraft";
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

function getAuthenticatedUserId() {
  if (!getAccessToken()) return "";
  try {
    const raw = sessionStorage.getItem("crown_current_user") || sessionStorage.getItem("crown_user");
    const user = raw ? JSON.parse(raw) : null;
    const value = user?.id ?? user?.user?.id;
    if (typeof value !== "number" && typeof value !== "string") return "";
    const id = String(value).trim();
    return id && id !== "None" && id !== "null" ? id : "";
  } catch { return ""; }
}

function SchoolFinancialAidWizard({ schoolId, userId }) {
  const [initialContext] = useState(() => ({}));
  const draftKey = "financial-aid-setup:" + schoolId + ":" + userId;
  const { value, saveDraft, loaded } = useWizardDraft(draftKey, initialContext, { storage: "session" });
  if (!loaded) return null;
  return (
    <CrownLayout title="Financial Aid Setup" subtitle="Configure aid year, active buckets, and create awards for the aid cycle">
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <CrownWizard
          stepComponents={STEP_COMPONENTS}
          stepLabels={STEP_LABELS}
          initialContext={value}
          onContextChange={saveDraft}
          stepProps={{ draftKey }}
        />
      </div>
    </CrownLayout>
  );
}

export default function FinancialAidWizard() {
  const [scope, setScope] = useState(() => ({
    schoolId: getSelectedSchoolId(),
    userId: getAuthenticatedUserId(),
    authVersion: 0,
  }));
  useEffect(() => {
    // Older local drafts have no reliable staff ownership and are never migrated.
    clearFinancialAidWizardDrafts({ includeSession: false });
    const updateSchool = () => setScope((previous) => ({
      ...previous,
      schoolId: getSelectedSchoolId(),
      userId: getAuthenticatedUserId(),
    }));
    const updateAuth = () => setScope((previous) => ({
      schoolId: getSelectedSchoolId(),
      userId: getAuthenticatedUserId(),
      authVersion: previous.authVersion + 1,
    }));
    window.addEventListener(SCHOOL_CONTEXT_CHANGE_EVENT, updateSchool);
    window.addEventListener(AUTH_CONTEXT_CHANGE_EVENT, updateAuth);
    return () => {
      window.removeEventListener(SCHOOL_CONTEXT_CHANGE_EVENT, updateSchool);
      window.removeEventListener(AUTH_CONTEXT_CHANGE_EVENT, updateAuth);
    };
  }, []);
  if (!scope.schoolId) return (
    <CrownLayout title="Financial Aid Setup">
      <div role="alert" className="crown-alert crown-alert--error">Select a school to configure financial aid.</div>
    </CrownLayout>
  );
  if (!scope.userId) return (
    <CrownLayout title="Financial Aid Setup">
      <div role="alert" className="crown-alert crown-alert--error">
        Sign in with a verified school staff identity to configure financial aid.
      </div>
    </CrownLayout>
  );
  return <SchoolFinancialAidWizard key={scope.schoolId + ":" + scope.userId + ":" + scope.authVersion}
    schoolId={scope.schoolId} userId={scope.userId} />;
}
