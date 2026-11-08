/** Truthful classroom summary: metrics refer only to rows returned by the
 * selected school's authorized list endpoint. No illustrative counts.
 */
const makeKpi = (label, value, definition) => ({
  label,
  value,
  trend: null,
  trendUp: null,
  definition,
  dataSource: "Classroom list API",
  dataHref: "/classrooms",
});

export function buildClassroomKpis({ classrooms, loading, error } = {}) {
  const available = !loading && !error && Array.isArray(classrooms);
  const rows = available ? classrooms : [];
  const unknown = "—";
  const rosterCountsKnown = available && rows.every(
    (item) => Number.isInteger(item?.student_count) && item.student_count >= 0,
  );
  const assignedHomerooms = rows.filter(
    (item) => typeof item?.homeroom_teacher_name === "string"
      && item.homeroom_teacher_name.trim().length > 0,
  ).length;

  return [
    makeKpi(
      "Active classrooms",
      available ? String(rows.length) : unknown,
      "Active classroom records returned by this school's authorized classroom list; no demo estimates.",
    ),
    makeKpi(
      "Roster entries",
      rosterCountsKnown ? String(rows.reduce((sum, row) => sum + row.student_count, 0)) : unknown,
      "Sum of classroom roster memberships. A student in multiple classrooms may be counted more than once.",
    ),
    makeKpi(
      "Homerooms staffed",
      available ? String(assignedHomerooms) : unknown,
      "Active classroom records with a named homeroom teacher; this is not a count of unique teachers.",
    ),
  ];
}
