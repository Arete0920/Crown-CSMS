export type CertificationTenant = {
  id: string;
  schoolKey: string;
  label: string;
  schoolId: string;
};

const DEFAULT_HERITAGE_SCHOOL_UUID = "19801b59-8c05-4c84-9312-5d792e4e839d";
const LIVE_SCHOOL_ID = process.env.CROWN_LIVE_SCHOOL_ID?.trim();
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID?.trim();

const certificationSchoolId = LIVE_SCHOOL_ID || DEMO_SCHOOL_ID || DEFAULT_HERITAGE_SCHOOL_UUID;
const certificationSchoolLabel = LIVE_SCHOOL_ID
  ? process.env.CROWN_LIVE_SCHOOL_LABEL?.trim() || "Production certification school"
  : "Heritage Christian Academy";

export const certificationTenants: CertificationTenant[] = [
  {
    id: "heritage",
    schoolKey: "heritage-core",
    label: certificationSchoolLabel,
    schoolId: certificationSchoolId,
  },
];
