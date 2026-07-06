export type CertificationTenant = {
  id: string;
  schoolKey: string;
  label: string;
  schoolId: string;
};

const DEFAULT_HERITAGE_SCHOOL_UUID = "19801b59-8c05-4c84-9312-5d792e4e839d";
const TENANT_MODE = (process.env.CROWN_CERTIFICATION_TENANT_MODE || "sandbox").trim().toLowerCase();
const USES_LIVE_TENANT = TENANT_MODE === "live";
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID?.trim();
const LIVE_SCHOOL_ID = process.env.CROWN_LIVE_SCHOOL_ID?.trim();
const LIVE_SCHOOL_LABEL = process.env.CROWN_LIVE_SCHOOL_LABEL?.trim();

if (USES_LIVE_TENANT && !LIVE_SCHOOL_ID) {
  throw new Error("CROWN_LIVE_SCHOOL_ID is required when CROWN_CERTIFICATION_TENANT_MODE=live.");
}

const certificationSchoolId = USES_LIVE_TENANT
  ? LIVE_SCHOOL_ID
  : DEMO_SCHOOL_ID || DEFAULT_HERITAGE_SCHOOL_UUID;
const certificationSchoolLabel = USES_LIVE_TENANT
  ? LIVE_SCHOOL_LABEL || "Live certification school"
  : "Heritage Christian Academy";

export const certificationTenants: CertificationTenant[] = [
  {
    id: "heritage",
    schoolKey: "heritage-core",
    label: certificationSchoolLabel,
    schoolId: certificationSchoolId,
  },
];
