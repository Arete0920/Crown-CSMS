export const KPI_REGISTRY = [
  {
    id: "enrollment_total",
    title: "Total Enrollment",
    sourceEndpoint: "/api/students/summary/",
    route: "/students",
    filters: { status: "active" },
    actions: [
      { label: "View students", route: "/students" },
      { label: "Review re-enrollment", route: "/enrollment", filters: { status: "pending" } },
    ],
  },
  {
    id: "attendance_today",
    title: "Attendance Today",
    sourceEndpoint: "/api/attendance/today-summary/",
    route: "/attendance",
    filters: { date: "today" },
    actions: [
      { label: "Open attendance", route: "/attendance" },
      { label: "Message families", route: "/messages", filters: { template: "attendance" } },
    ],
  },
  {
    id: "past_due_families",
    title: "Past Due Families",
    sourceEndpoint: "/api/finance/ar-aging-summary/",
    route: "/finance/accounts-receivable",
    filters: { status: "past_due" },
    actions: [
      { label: "Review A/R", route: "/finance/accounts-receivable", filters: { status: "past_due" } },
    ],
  },
  {
    id: "academic_risk_students",
    title: "Academic Risk",
    sourceEndpoint: "/api/student360/risk-summary/",
    route: "/student360",
    filters: { risk: "high" },
    actions: [
      { label: "View students", route: "/student360", filters: { risk: "high" } },
    ],
  },
  {
    id: "compliance_items",
    title: "Compliance Items",
    sourceEndpoint: "/api/compliance/items-summary/",
    route: "/compliance-audit-dashboard",
    filters: { status: "open" },
    actions: [
      { label: "Open compliance", route: "/compliance-audit-dashboard" },
    ],
  },
];

export function buildKpiRoute(kpi) {
  const path = kpi.route || kpi.path;
  const params = new URLSearchParams();

  Object.entries(kpi.filters || {}).forEach(([key, value]) => {
    params.set(key, String(value));
  });

  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}
