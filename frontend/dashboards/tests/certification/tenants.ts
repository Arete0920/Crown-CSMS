export type CertificationTenant = {
  id: string;
  schoolKey: string;
  label: string;
  schoolId: string;
};

const HERITAGE_SCHOOL_UUID = "19801b59-8c05-4c84-9312-5d792e4e839d";

export const certificationTenants: CertificationTenant[] = [
  { id: "heritage", schoolKey: "heritage-core", label: "Heritage Christian Academy", schoolId: HERITAGE_SCHOOL_UUID },
];
