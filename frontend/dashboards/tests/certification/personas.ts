export type CertificationPersona = {
  id: string;
  label: string;
  role: string;
};

export const certificationPersonas: CertificationPersona[] = [
  { id: "sandbox-admin", label: "Sandbox Admin", role: "admin" },
  { id: "sandbox-teacher", label: "Sandbox Teacher", role: "teacher" },
  { id: "sandbox-parent", label: "Sandbox Parent", role: "parent" },
  { id: "sandbox-student", label: "Sandbox Student", role: "student" },
  { id: "sandbox-board", label: "Sandbox Board", role: "board" },
];
