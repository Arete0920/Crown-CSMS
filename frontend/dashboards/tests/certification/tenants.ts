export type CertificationTenant = {
  id: string;
  label: string;
  schoolCode: string;
  schoolId: string;
};

const HERITAGE_DEMO_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d";

export const certificationTenants: CertificationTenant[] = [
  { id: "heritage", label: "Heritage Christian Academy", schoolCode: "heritage", schoolId: HERITAGE_DEMO_SCHOOL_ID },
];
