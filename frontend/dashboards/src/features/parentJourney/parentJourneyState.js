import { apiFetch } from "../../lib/api";

const PARENT_OVERVIEW_PATH = "/api/v1/parent360/me/overview/";

let overviewPromise = null;

function getApplications(overview) {
  return Array.isArray(overview?.applications) ? overview.applications : [];
}

function hasLifecycleStage(applications, lifecycleStages) {
  return applications.some((application) => lifecycleStages.includes(application?.lifecycle_stage));
}

export async function loadParentJourneyOverview() {
  if (!overviewPromise) {
    overviewPromise = apiFetch(PARENT_OVERVIEW_PATH).catch((error) => {
      overviewPromise = null;
      throw error;
    });
  }

  return overviewPromise;
}

export function canAccessParentJourneyStage(stage, overview) {
  const applications = getApplications(overview);

  if (!applications.length) {
    return stage === "status";
  }

  switch (stage) {
    case "billing":
      return hasLifecycleStage(applications, ["accepted", "enrolled"]);

    case "billingPay":
      return applications.some((application) => {
        const lifecycleReady = ["accepted", "enrolled"].includes(application?.lifecycle_stage);
        const paymentReady = application?.payment_precheck?.status === "ready"
          || application?.payment_precheck?.contract_ready
          || application?.payment_precheck?.deposit_ready;

        return lifecycleReady && paymentReady;
      });

    case "aid":
      return applications.some((application) => {
        const aidStatus = application?.financial_aid_status || "";

        return aidStatus !== "Not Applying"
          || ["submitted", "in_review", "accepted", "enrolled"].includes(application?.lifecycle_stage);
      });

    case "status":
      return true;

    case "classAssignment":
      return applications.some((application) => {
        return application?.lifecycle_stage === "enrolled"
          || application?.classroom_readiness_status === "in_progress"
          || application?.classroom_readiness_status === "completed";
      });

    case "activeStudent":
      return applications.some((application) => {
        return application?.lifecycle_stage === "enrolled"
          || application?.applicant_to_student_status === "completed"
          || application?.parent_portal_activation_status === "in_progress";
      });

    default:
      return true;
  }
}
