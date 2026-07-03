export type CertificationTenant = {
  id: string;
  label: string;
  schoolCode: string;
  schoolId: string;
};

export const certificationTenants: CertificationTenant[] = [
  { id: "heritage", label: "Heritage Christian Academy", schoolCode: "heritage", schoolId: "heritage" },
];
