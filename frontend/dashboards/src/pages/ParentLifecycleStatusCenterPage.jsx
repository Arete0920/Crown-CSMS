import ParentJourneyOverviewPage from "../features/parentJourney/ParentJourneyOverviewPage.jsx";
import ParentSandboxEnrollmentPanel from "../features/parentJourney/ParentSandboxEnrollmentPanel.jsx";

export default function ParentLifecycleStatusCenterPage() {
  return (
    <>
      <ParentJourneyOverviewPage focus="status" />
      <ParentSandboxEnrollmentPanel />
    </>
  );
}
